"""代码重排序模块 — 对 Top-K 检索结果用 Rerank 模型 API 二次精排。

理论：双阶段检索（two-stage retrieval）。
- 一阶段粗排（HybridRetriever）：BM25 + 向量，追求召回率，故意多召回
- 二阶段精排（本模块）：cross-encoder 对 [query, doc] 对打分，追求精确率
"""

import logging
from typing import Any

from langchain_classic.retrievers.contextual_compression import (
    ContextualCompressionRetriever,
)
from langchain_cohere import CohereRerank
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from deeprag_coder.config.settings import get_settings

logger = logging.getLogger(__name__)


class CodeReranker:
    """对 HybridRetriever 召回的 Top-K 文档调用 Rerank 模型二次精排。

    示例:
        >>> reranker = CodeReranker()
        >>> docs = hybrid.invoke("JWT 鉴权")
        >>> top5 = reranker.rerank("JWT 鉴权", docs)
    """

    compressor: CohereRerank
    top_n: int

    def __init__(
        self,
        model: str | None = None,
        top_n: int | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        """初始化 CodeReranker 实例。

        Args:
            model: Rerank 模型名，默认从配置读取。
            top_n: 精排后保留条数，默认从配置读取。
            api_key: Cohere API Key，默认从配置读取。
            base_url: 可选自定义 rerank 端点（Cohere 协议兼容的 /v1/rerank）。
        """
        cfg = get_settings().rerank
        selected_model = model or cfg.model
        selected_top_n = top_n or cfg.top_n
        selected_key = api_key or cfg.api_key
        selected_url = base_url or cfg.base_url

        if not selected_key:
            raise ValueError(
                "Rerank API Key 缺失：请在 .env 中设置 cohere_api_key，"
                "或将 rerank_enabled 设为 false 关闭重排。"
            )

        kwargs: dict[str, Any] = {
            "model": selected_model,
            "top_n": selected_top_n,
            "cohere_api_key": selected_key,
        }
        if selected_url:
            # 指向自建/第三方 Cohere 协议兼容端点
            kwargs["base_url"] = selected_url

        self.compressor = CohereRerank(**kwargs)
        self.top_n = selected_top_n
        logger.info(
            "CodeReranker 就绪: model=%s, top_n=%d, base_url=%s",
            selected_model,
            selected_top_n,
            selected_url or "cohere-cloud",
        )

    def rerank(self, query: str, docs: list[Document]) -> list[Document]:
        """对 docs 列表用 rerank 模型重排并截取 top_n。

        Args:
            query: 用户查询文本。
            docs: 粗排返回的 Top-K 候选文档。

        Returns:
            按 relevance_score 降序排列的 top_n 文档列表。
        """
        if not docs:
            return []
        # compress_documents 内部调用 Cohere /v1/rerank，返回已排序的 top_n 文档
        return self.compressor.compress_documents(docs, query)


def compose_rerank_retriever(
    base_retriever: BaseRetriever,
    reranker: CodeReranker,
) -> ContextualCompressionRetriever:
    """把任意 BaseRetriever 包成 "粗排 + 精排" 复合检索器（官方模式）。

    Args:
        base_retriever: 已有粗检索器（须实现 BaseRetriever 接口）。
        reranker: 已初始化的 CodeReranker 实例。

    Returns:
        ContextualCompressionRetriever 复合检索器。
    """
    return ContextualCompressionRetriever(
        base_compressor=reranker.compressor,
        base_retriever=base_retriever,
    )
