"""RAG 管道总控 — 索引 + 检索 + 问答的完整编排。"""

import logging
from pathlib import Path

import networkx as nx
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI

from deeprag_coder.config.settings import get_settings
from deeprag_coder.rag.chunker.semantic_chunker import SemanticChunker
from deeprag_coder.rag.context_assembler import assemble_context
from deeprag_coder.rag.embedder.code_embedder import CodeEmbedder
from deeprag_coder.rag.knowledge_graph.builder import KnowledgeGraphBuilder
from deeprag_coder.rag.retriever.hybrid_retriever import HybridRetriever
from deeprag_coder.rag.retriever.reranker import CodeReranker
from deeprag_coder.rag.vector_store.chroma_store import ChromaStore
from deeprag_coder.utils.repo_map import generate_repo_map

logger = logging.getLogger(__name__)

IGNORE_DIRS = frozenset(
    {
        ".git",
        ".venv",
        "__pycache__",
        "node_modules",
        ".tox",
        ".idea",
        ".vscode",
        "dist",
        "build",
        ".egg-info",
    }
)
CODE_EXTENSIONS = frozenset(
    {
        ".py",
        ".ts",
        ".js",
        ".go",
        ".java",
        ".rs",
        ".c",
        ".h",
        ".cpp",
        ".rb",
        ".cs",
        ".swift",
        ".kt",
    }
)


class RAGPipeline:
    """RAG 管道总控。

    用法:
        >>> pipe = RAGPipeline("./my-repo")
        >>> pipe.index_repo()
        >>> docs = pipe.search("JWT 认证")
        >>> answer = pipe.ask("JWT 认证流程是什么")
    """

    def __init__(
        self,
        repo_path: str | Path = "",
        reranker: CodeReranker | None = None,
    ) -> None:
        cfg = get_settings()
        self.repo_path = Path(repo_path or cfg.repo_path)
        self.chunker = SemanticChunker()
        self.embedder = CodeEmbedder()
        self.store = ChromaStore()
        self.hybrid: HybridRetriever | None = None
        self.reranker = reranker

    def index_repo(self) -> int:
        """扫描仓库，分块 → 嵌入 → 存储 → BM25 拟合。

        Returns:
            索引的 chunk 总数。
        """
        files = self._scan_files()
        logger.info("扫描到 %d 个代码文件", len(files))

        all_chunks = self.chunker.chunk_files(files)
        logger.info("分块完成: %d 个 chunk", len(all_chunks))

        vectors = self.embedder.embed_chunks(all_chunks)
        self.store.add_from_chunks(all_chunks, vectors)
        logger.info("向量已写入 ChromaDB")

        self.hybrid = HybridRetriever(chroma_store=self.store)
        self.hybrid.fit_bm25(all_chunks)
        logger.info("BM25 索引拟合完成")

        return len(all_chunks)

    def search(self, query: str, top_k: int = 10) -> list[Document]:
        """检索相关代码片段。"""
        if self.hybrid is None:
            raise RuntimeError("请先调用 index_repo() 初始化索引")
        docs = self.hybrid.invoke(query)
        if self.reranker:
            docs = self.reranker.rerank(query, docs)
        return docs[:top_k]

    def ask(self, query: str) -> str:
        """检索 + LLM 问答（使用 Context Assembler 组装 prompt）。"""
        docs = self.search(query)
        repo_map = generate_repo_map(self.repo_path, max_files=30)
        prompt = assemble_context(query, docs, repo_map=repo_map)
        cfg = get_settings()
        llm = ChatOpenAI(
            model=cfg.llm.model,
            api_key=cfg.llm.api_key,
            base_url=cfg.llm.base_url,
            temperature=0,
        )
        return llm.invoke(prompt).content

    def _scan_files(self) -> list[Path]:
        files = []
        for fp in self.repo_path.rglob("*"):
            if not fp.is_file():
                continue
            if any(
                part.startswith(".") for part in fp.relative_to(self.repo_path).parts
            ):
                continue
            if fp.suffix in CODE_EXTENSIONS:
                files.append(fp)
        return files


# 文件末尾或顶部加

_pipeline: RAGPipeline | None = None
_graph: nx.DiGraph | None = None


def init_rag(repo_path: str | Path = "") -> int:
    """初始化 RAG 索引 + 知识图谱，全局共享。

    Args:
        repo_path: 仓库根路径。

    Returns:
        索引的 chunk 数。
    """
    global _pipeline, _graph
    _pipeline = RAGPipeline(repo_path)
    n = _pipeline.index_repo()

    _graph = KnowledgeGraphBuilder().build(_pipeline.repo_path)
    return n


def get_pipeline() -> RAGPipeline:
    if _pipeline is None:
        raise RuntimeError("请先调用 init_rag()")
    return _pipeline


def get_graph() -> nx.DiGraph:
    if _graph is None:
        raise RuntimeError("请先调用 init_rag()")
    return _graph
