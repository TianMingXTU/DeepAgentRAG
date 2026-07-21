"""知识图谱构建器 — 从 AST 提取符号和调用关系，构建内存有向图。
 
 使用 networkx.DiGraph，节点 = 函数/类符号，边 = 调用关系。
"""
 
import logging
from pathlib import Path
 
import networkx as nx
from langchain_openai import ChatOpenAI
from tree_sitter import Node as TSNode
 
from deeprag_coder.config.settings import get_settings
from deeprag_coder.rag.chunker.ast_parser import ASTParser, ParsedFile

logger = logging.getLogger(__name__)

# 调用节点类型（tree-sitter 语法树中的 call 表达式）
CALL_NODE_TYPES: frozenset[str] = frozenset(
    {
        "call",  # Python / JS / TS / Go / Rust
        "method_invocation",  # Java
    }
)

# Python 中 "调用者" 的父节点——函数体、方法体
FUNCTION_BODY_TYPES: frozenset[str] = frozenset(
    {
        "block",  # Python 函数体
        "body",  # JS/TS 函数体
    }
)


class KnowledgeGraphBuilder:
    """从代码仓库构建调用关系知识图谱。

    用法:
        >>> builder = KnowledgeGraphBuilder()
        >>> G = builder.build(Path("./my-repo"))
        >>> len(G.nodes), len(G.edges)
    """

    def __init__(self) -> None:
        self._parser = ASTParser()

    def build(self, repo_path: Path) -> nx.DiGraph:
        """扫描仓库，构建调用关系有向图。

        Args:
            repo_path: 仓库根目录路径。

        Returns:
            networkx.DiGraph，节点属性含 name/kind/file/line/docstring。
        """
        G = nx.DiGraph()
        all_blocks: list[tuple[ParsedFile, list]] = []

        for fp in sorted(repo_path.rglob("*")):
            if not fp.is_file():
                continue
            rel = fp.relative_to(repo_path)
            if any(part.startswith(".") for part in rel.parts):
                continue
            parsed = self._parser.parse(fp)
            if parsed.error or not parsed.blocks:
                continue
            all_blocks.append((parsed, parsed.blocks))

            # 添加符号节点
            for blk in parsed.blocks:
                if not blk.symbol_name:
                    continue
                G.add_node(
                    blk.symbol_name,
                    name=blk.symbol_name,
                    kind=blk.node_type,
                    file=str(blk.file_path),
                    line=blk.start_line,
                )
                # 父子关系（class → method）
                if blk.parent_name:
                    G.add_edge(blk.parent_name, blk.symbol_name, type="contains")

        # 提取调用关系
        for parsed, blocks in all_blocks:
            src_bytes = parsed.source.encode("utf-8")
            for blk in blocks:
                if not blk.symbol_name:
                    continue
                # 用 tree-sitter 重新找到该节点，遍历其子节点中的 calls
                tree = self._parser._parsers.get(parsed.language)
                if not tree:
                    continue
                # 重新解析一次获取树
                try:
                    t = tree.parse(src_bytes)
                except Exception:
                    continue
                calls = self._extract_calls(
                    t.root_node, blk.start_line, blk.end_line, src_bytes
                )
                for callee in calls:
                    if callee != blk.symbol_name:  # 避免自环
                        G.add_edge(blk.symbol_name, callee, type="calls")

        logger.info(
            "知识图谱构建完成: %d 节点, %d 边",
            G.number_of_nodes(),
            G.number_of_edges(),
        )
        return G

    def enrich_with_summaries(
        self, G: nx.DiGraph, batch_size: int = 10
    ) -> nx.DiGraph:
        """为关键符号生成 LLM 语义摘要，写入节点属性。

        Args:
            G: 已有调用关系图。
            batch_size: 每批摘要的符号数（控制 API 调用成本）。

        Returns:
            追加了 'summary' 属性的图。
        """
        cfg = get_settings()
        llm = ChatOpenAI(
            model=cfg.llm.model,
            api_key=cfg.llm.api_key,
            base_url=cfg.llm.base_url,
            temperature=0,
        )
        # 选出度/入度最高的符号（核心枢纽节点）
        scored = [
            (n, G.out_degree(n) + G.in_degree(n)) for n in G.nodes
        ]
        scored.sort(key=lambda x: -x[1])
        top_symbols = [n for n, _ in scored[:batch_size]]

        for sym in top_symbols:
            node = G.nodes[sym]
            kind = node.get("kind", "symbol")
            prompt = (
                f"Summarize the purpose of this {kind} `{sym}` in one sentence "
                f"(file: {node.get('file', '?')}). Keep under 30 words."
            )
            try:
                summary = llm.invoke(prompt).content.strip()
                G.nodes[sym]["summary"] = summary
            except Exception as e:
                logger.warning("摘要生成失败 %s: %s", sym, e)
        return G

    def _extract_calls(
        self,
        node: TSNode,
        start_line: int,
        end_line: int,
        src: bytes,
    ) -> list[str]:
        """在指定行范围内提取所有被调用函数名。"""
        calls: list[str] = []

        def walk(n: TSNode) -> None:
            sr = n.start_point[0] + 1
            er = n.end_point[0] + 1
            if sr > end_line:
                return
            if er < start_line:
                return

            if n.type in CALL_NODE_TYPES:
                name = self._resolve_call_name(n, src)
                if name:
                    calls.append(name)

            for child in n.children:
                walk(child)

        walk(node)
        return calls

    def _resolve_call_name(self, node: TSNode, src: bytes) -> str | None:
        """从 call 节点提取被调函数名。

        处理:
          - foo()          → "foo"
          - self.bar()     → "bar"
          - module.func()  → "module.func"
        """
        try:
            func_node = node.child_by_field_name("function")
            if func_node is None:
                return None

            # 简单 identifier: foo()
            if func_node.type == "identifier":
                return src[func_node.start_byte : func_node.end_byte].decode("utf-8")

            # 属性访问: self.bar() / module.func()
            if func_node.type == "attribute":
                obj = func_node.child_by_field_name("object")
                attr = func_node.child_by_field_name("attribute")
                if attr and attr.type == "identifier":
                    return src[attr.start_byte : attr.end_byte].decode("utf-8")

            # 链式: a.b.c() — 取最后一段
            return None
        except Exception:
            return None
