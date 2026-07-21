"""混合检索器模块 — 结合语义向量检索与 BM25 关键词检索。

通过加权融合（Ensemble / RRF）实现更鲁棒的代码召回效果。
"""

import logging
from typing import Any, Sequence

from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from deeprag_coder.config.settings import get_settings
from deeprag_coder.rag.embedder.code_embedder import CodeEmbedder
from deeprag_coder.rag.vector_store.base import VectorRecord
from deeprag_coder.rag.vector_store.chroma_store import ChromaStore
from deeprag_coder.rag.chunker.semantic_chunker import Chunk

logger = logging.getLogger(__name__)


class ChromaRetrieverAdapter(BaseRetriever):
    """将底层 ChromaStore 包装为符合 LangChain BaseRetriever 接口的适配器。

    Attributes:
        chroma_store: 已经建立索引的底层 ChromaStore 实例。
        embedder: 代码嵌入器实例，用于将查询字符串转化为高维向量。
        top_k: 向量检索返回的最大结果条数。
        filter_: 可选的元数据过滤条件（传递给 ChromaDB 的 where 参数）。
    """

    chroma_store: ChromaStore
    embedder: CodeEmbedder
    top_k: int = 10
    filter_: dict | None = None

    def __init__(
        self,
        chroma_store: ChromaStore,
        embedder: CodeEmbedder | None = None,
        top_k: int = 10,
        filter_: dict | None = None,
        **kwargs: Any,
    ) -> None:
        """初始化适配器实例。

        Args:
            chroma_store: 已接入数据索引的 ChromaStore 实例。
            embedder: 统一的代码嵌入器。若为 None，则创建新的 CodeEmbedder 单例。
            top_k: 向量检索返回数量。
            filter_: 可选的元数据过滤条件。
            **kwargs: 传递给父类 BaseRetriever / Pydantic 的额外字段。
        """
        # 将依赖项正确传入 Pydantic 模型基类
        super().__init__(
            chroma_store=chroma_store,
            embedder=embedder or CodeEmbedder(),
            top_k=top_k,
            filter_=filter_,
            **kwargs,
        )

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:
        """执行向量检索的核心回调逻辑。

        将文本查询转换为向量，委托给 ChromaStore 检索，并转换为 Document 对象。

        Args:
            query: 用户输入的自然语言或代码查询字符串。
            run_manager: LangChain 运行时回调管理器。

        Returns:
            符合 LangChain 规范的 Document 实例列表。
        """
        # 1. 使用注入的 embedder 单例生成查询向量
        query_vector = self.embedder.embed_one(query)

        # 2. 执行底层 ChromaStore 搜索
        records: list[VectorRecord] = self.chroma_store.search(
            query_vector=query_vector,
            top_k=self.top_k,
            filter_=self.filter_,
        )

        # 3. 数据结构映射: VectorRecord -> Document
        return [
            Document(
                page_content=record.text,
                metadata=record.metadata,
            )
            for record in records
        ]


class HybridRetriever:
    """混合检索器 — 结合 BM25 关键词检索与语义向量检索的加权融合。

    示例:
        >>> retriever = HybridRetriever(chroma_store=store, top_k=10)
        >>> retriever.fit_bm25(all_chunks=[...])
        >>> docs = retriever.invoke("JWT 认证实现")
    """

    def __init__(
        self,
        chroma_store: ChromaStore,
        embedder: CodeEmbedder | None = None,
        top_k: int | None = None,
        bm25_weight: float | None = None,
        vector_weight: float | None = None,
        bm25_k: int | None = None,
        vector_k: int | None = None,
    ) -> None:
        """初始化混合检索器。

        Args:
            chroma_store: 已接入数据索引的 ChromaStore 实例。
            embedder: 统一的代码嵌入器实例。
            top_k: 最终融合后返回给用户的结果数量。
            bm25_weight: BM25 分路在 Ensemble 融合中的权重（范围 0~1）。
            vector_weight: 向量分路在 Ensemble 融合中的权重（范围 0~1）。
            bm25_k: BM25 检索器内部返回的候选集数量（建议为 top_k 的 2 倍）。
            vector_k: 向量检索器内部返回的候选集数量（建议为 top_k 的 2 倍）。
        """
        cfg = get_settings().rag

        self.chroma_store = chroma_store
        self.embedder = embedder or CodeEmbedder()
        self.top_k = top_k or cfg.top_k

        self.bm25_weight = bm25_weight if bm25_weight is not None else cfg.bm25_weight
        self.vector_weight = (
            vector_weight if vector_weight is not None else cfg.semantic_weight
        )

        self.bm25_k = bm25_k or (self.top_k * 2)
        self.vector_k = vector_k or (self.top_k * 2)

        # 实例化向量路适配器
        self.vector_retriever = ChromaRetrieverAdapter(
            chroma_store=self.chroma_store,
            embedder=self.embedder,
            top_k=self.vector_k,
        )

        # BM25 检索器延迟加载，待调用 fit_bm25 时初始化
        self.bm25_retriever: BM25Retriever | None = None

    def fit_bm25(self, all_chunks: Sequence[Chunk]) -> None:
        """使用全量代码块 Chunk 拟合 BM25 索引。

        Args:
            all_chunks: 包含全局代码语料的 Chunk 对象序列。
        """
        if not all_chunks:
            logger.warning("传入的 Chunk 序列为空，跳过 BM25 索引拟合。")
            return

        documents = [
            Document(
                page_content=chunk.content,
                metadata=chunk.metadata,
            )
            for chunk in all_chunks
        ]

        self.bm25_retriever = BM25Retriever.from_documents(documents)
        self.bm25_retriever.k = self.bm25_k
        logger.info("BM25 索引成功拟合，文档总数: %d", len(documents))

    def invoke(self, query: str) -> list[Document]:
        """执行混合检索并返回融合排序后的文档。

        Args:
            query: 用户输入的查询文本。

        Returns:
            按相似度降序排列的最终 Document 结果列表。
        """
        # 降级策略: 当 BM25 未完成拟合时，回退至纯向量检索
        if self.bm25_retriever is None:
            logger.warning("BM25 尚未进行 fit_bm25 拟合，系统降级为纯语义向量检索。")
            results = self.vector_retriever.invoke(query)
            return results[: self.top_k]

        # 正常流程: 使用 EnsembleRetriever 进行加权融合
        ensemble = EnsembleRetriever(
            retrievers=[self.bm25_retriever, self.vector_retriever],
            weights=[self.bm25_weight, self.vector_weight],
        )
        return ensemble.invoke(query)[: self.top_k]

    def __call__(self, query: str) -> list[Document]:
        """允许直接将实例作为函数进行调用。

        Args:
            query: 查询字符串。

        Returns:
            检索到的 Document 列表。
        """
        return self.invoke(query)
