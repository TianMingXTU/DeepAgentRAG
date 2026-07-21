"""AST 解析器 — tree-sitter 封装，按语义边界抽取函数/类/方法。"""

import importlib
from dataclasses import dataclass, field
from pathlib import Path
import tempfile

from tree_sitter import Language, Parser

from tree_sitter import Node, Tree

# 扩展名 → (tree-sitter 语言标识, 对应的 PyPI 包名)
EXT_TO_LANG_INFO: dict[str, tuple[str, str]] = {
    ".py": ("python", "tree_sitter_python"),
    ".pyi": ("python", "tree_sitter_python"),
    ".ts": ("typescript", "tree_sitter_typescript"),
    ".tsx": ("tsx", "tree_sitter_typescript"),
    ".js": ("javascript", "tree_sitter_javascript"),
    ".jsx": ("javascript", "tree_sitter_javascript"),
    ".go": ("go", "tree_sitter_go"),
    ".java": ("java", "tree_sitter_java"),
    ".rs": ("rust", "tree_sitter_rust"),
    ".c": ("c", "tree_sitter_c"),
    ".h": ("c", "tree_sitter_c"),
    ".cpp": ("cpp", "tree_sitter_cpp"),
    ".hpp": ("cpp", "tree_sitter_cpp"),
    ".cc": ("cpp", "tree_sitter_cpp"),
    ".rb": ("ruby", "tree_sitter_ruby"),
    ".cs": ("c_sharp", "tree_sitter_c_sharp"),
    ".swift": ("swift", "tree_sitter_swift"),
    ".kt": ("kotlin", "tree_sitter_kotlin"),
    ".php": ("php", "tree_sitter_php"),
    ".sql": ("sql", "tree_sitter_sql"),
    ".sh": ("bash", "tree_sitter_bash"),
    ".bash": ("bash", "tree_sitter_bash"),
    ".toml": ("toml", "tree_sitter_toml"),
    ".yaml": ("yaml", "tree_sitter_yaml"),
    ".yml": ("yaml", "tree_sitter_yaml"),
    ".md": ("markdown", "tree_sitter_markdown"),
}

# 哪些 tree-sitter 节点类型视为“一个语义单元”
SEMANTIC_NODE_TYPES: frozenset[str] = frozenset(
    {
        # Python
        "function_definition",
        "class_definition",
        "async_function_definition",
        # JS/TS
        "function_declaration",
        "method_definition",
        "class_declaration",
        "arrow_function",
        # Go
        "function_declaration",
        "method_declaration",
        # Java
        "method_declaration",
        "class_declaration",
        "constructor_declaration",
        # Rust
        "function_item",
        "impl_item",
        "struct_item",
        "trait_item",
        "enum_item",
    }
)


@dataclass
class CodeBlock:
    """AST 抽出的单个语义块（函数/类/方法）。"""

    file_path: Path
    symbol_name: str | None
    node_type: str
    start_line: int  # 1-indexed
    end_line: int
    content: str
    parent_name: str | None = None


@dataclass
class ParsedFile:
    """一个文件解析后的产出。"""

    file_path: Path
    language: str
    source: str = ""
    lines: list[str] = field(default_factory=list)
    blocks: list[CodeBlock] = field(default_factory=list)
    error: str | None = None


class ASTParser:

    def __init__(self) -> None:
        # 存储已初始化的 Parser 实例
        self._parsers: dict[str, Parser] = {}

        # 预热常见语言 parser（支持的语言需要安装对应的 PyPI 包，例如 `pip install tree-sitter-python`）
        for lang in ("python", "typescript", "go", "java", "rust"):
            self._build_parser(lang)

    def _get_package_name_for_lang(self, lang: str) -> str | None:
        """根据语言标识反向推导或查找对应的 tree_sitter_* 包名。"""
        for _, (l, pkg) in EXT_TO_LANG_INFO.items():
            if l == lang:
                return pkg
        # 容错降级推导逻辑
        return f"tree_sitter_{lang}"

    def _build_parser(self, lang: str) -> None:
        """创建并缓存指定语言的 tree-sitter Parser 实例 (适配 tree-sitter >= 0.22.0)。"""
        pkg_name = self._get_package_name_for_lang(lang)
        if not pkg_name:
            return

        try:
            # 动态导入对应的 tree_sitter_<lang> 包
            mod = importlib.import_module(pkg_name)

            # tree_sitter_typescript 内部含有 language_typescript 和 language_tsx 细分
            if lang == "tsx" and hasattr(mod, "language_tsx"):
                lang_fn = getattr(mod, "language_tsx")
            elif hasattr(mod, f"language_{lang}"):
                lang_fn = getattr(mod, f"language_{lang}")
            elif hasattr(mod, "language"):
                lang_fn = getattr(mod, "language")
            else:
                return

            ts_lang = Language(lang_fn())

            # 适配 tree-sitter >= 0.22.0 API：通过 Parser(Language) 实例化
            parser = Parser(ts_lang)
            self._parsers[lang] = parser
        except Exception:
            # 加载失败（可能对应的 pip 包未安装），暂不处理，等待运行阶段报错或跳过
            pass

    @classmethod
    def detect_language(cls, fp: Path) -> str | None:
        """根据文件扩展名判断语言。"""
        info = EXT_TO_LANG_INFO.get(fp.suffix.lower())
        return info[0] if info else None

    def parse(self, fp: Path, source: str | None = None) -> ParsedFile:
        """解析单个文件，返回 ParsedFile（含语义块）。"""
        lang = self.detect_language(fp)
        parsed = ParsedFile(file_path=fp, language=lang or "??")

        if lang is None:
            parsed.error = f"Unsupported extension: {fp.suffix}"
            return parsed

        # 尝试动态加载 Parser
        if lang not in self._parsers:
            self._build_parser(lang)

        parser = self._parsers.get(lang)
        if parser is None:
            pkg_name = self._get_package_name_for_lang(lang)
            parsed.error = (
                f"No parser loaded for '{lang}'. "
                f"Please install the dependency: pip install {pkg_name.replace('_', '-')}"
            )
            return parsed

        # 读取源码
        try:
            src = (
                source
                if source is not None
                else fp.read_text(encoding="utf-8", errors="replace")
            )
        except Exception as e:
            parsed.error = f"IO error: {e}"
            return parsed

        parsed.source = src
        parsed.lines = src.splitlines()

        # tree-sitter 解析
        try:
            src_bytes = src.encode("utf-8")
            tree = parser.parse(src_bytes)
        except Exception as e:
            parsed.error = f"Syntax error: {e}"
            return parsed

        parsed.blocks = self._extract_blocks(tree, parsed, src_bytes)
        return parsed

    # --------- 内部工具 ----------

    def _extract_blocks(
        self, tree: Tree, pf: ParsedFile, src_bytes: bytes
    ) -> list[CodeBlock]:
        """遍历语法树，收集所有 SEMANTIC_NODE_TYPES 节点。"""
        blocks: list[CodeBlock] = []

        def walk(node: Node, parent: CodeBlock | None = None) -> None:
            nt = node.type
            current_parent = parent

            if nt in SEMANTIC_NODE_TYPES:
                sr = node.start_point[0] + 1  # 转换为 1-indexed
                er = node.end_point[0] + 1
                content = "\n".join(pf.lines[sr - 1 : er])
                name = self._resolve_name(node, src_bytes)

                blk = CodeBlock(
                    file_path=pf.file_path,
                    symbol_name=name,
                    node_type=nt,
                    start_line=sr,
                    end_line=er,
                    content=content,
                    parent_name=parent.symbol_name if parent else None,
                )
                blocks.append(blk)
                current_parent = blk  # 当前块作为其子节点的 parent（如类中的方法）

            for child in node.children:
                walk(child, current_parent)

        walk(tree.root_node)
        return blocks

    def _resolve_name(self, node: Node, src_bytes: bytes) -> str | None:
        """从 AST 节点取 'name' 字段（函数名/类名）。"""
        try:
            # 1. 优先采用 tree-sitter 的 child_by_field_name
            n = node.child_by_field_name("name")
            if n is not None:
                return src_bytes[n.start_byte : n.end_byte].decode("utf-8")

            # 2. 回退机制：部分节点的 identifier 并不叫 'name' 字段
            for child in node.children:
                if child.type in (
                    "identifier",
                    "type_identifier",
                    "property_identifier",
                ):
                    return src_bytes[child.start_byte : child.end_byte].decode("utf-8")
        except Exception:
            pass
        return None

    # --- 自检 ---
    @classmethod
    def demo(cls) -> None:
        sample = """def foo(): pass

class Bar:
    def baz(self): pass
"""
        fp = None
        try:
            with tempfile.NamedTemporaryFile(
                suffix=".py", mode="w", encoding="utf-8", delete=False
            ) as f:
                f.write(sample)
                fp = Path(f.name)

            parser = cls()
            pf = parser.parse(fp, source=sample)

            if pf.error:
                print(f"[FAIL] Error during parsing: {pf.error}")
                return

            assert len(pf.blocks) == 3, f"Expected 3 blocks, got {len(pf.blocks)}"
            names = {b.symbol_name for b in pf.blocks}
            assert names == {
                "foo",
                "Bar",
                "baz",
            }, f"Expected {{'foo', 'Bar', 'baz'}}, got {names}"

            print(f"[PASS] {len(pf.blocks)} blocks parsed, symbols={names}")

        finally:
            if fp and fp.exists():
                fp.unlink(missing_ok=True)


if __name__ == "__main__":
    ASTParser.demo()
