"""代码嵌入器模块 — 统一封装 LangChain OpenAIEmbeddings，支持自动分批与重试机制。"""

from typing import Sequence

from langchain_openai import OpenAIEmbeddings

from deeprag_coder.config.settings import get_settings

from deeprag_coder.rag.chunker.semantic_chunker import Chunk


class CodeEmbedder:
    """提供源代码文本及代码块（Chunk）的向量嵌入服务。

    Attributes:
        _client: 底层使用的 LangChain OpenAIEmbeddings 客户端实例。
    """

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        batch_size: int | None = None,
        max_retries: int = 3,
    ) -> None:
        """初始化 CodeEmbedder 实例。

        Args:
            model: 所使用的嵌入模型名称。若未指定，默认从全局配置获取。
            api_key: OpenAI API 密钥。若未指定，默认从全局配置获取。
            base_url: OpenAI API 基础服务地址。若未指定，默认从全局配置获取。
            batch_size: 单次 API 请求的最大文本数量（分批大小）。若未指定，默认从全局配置获取。
            max_retries: 请求失败时的最大重试次数，默认为 3 次。
        """
        cfg = get_settings()
        llm_cfg = cfg.llm
        rag_cfg = cfg.rag

        selected_model = model or rag_cfg.embedding_model
        chunk_size = batch_size or rag_cfg.embedding_batch_size

        # LangChain 原生支持 chunk_size（自动分批）与 max_retries（自动重试）
        self._client = OpenAIEmbeddings(
            model=selected_model,
            api_key=api_key or rag_cfg.embedding_api_key,
            base_url=base_url or rag_cfg.embedding_base_url,
            chunk_size=chunk_size,
            max_retries=max_retries,
            show_progress_bar=True,
        )

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """将文本序列批量转换为高维稠密向量。

        LangChain 内部会根据初始化时设置的 chunk_size 自动进行分批处理，无需手写循环。

        Args:
            texts: 待嵌入的文本字符串序列。

        Returns:
            浮点数列表的列表，每个子列表代表一个文本的向量表示。
        """
        if not texts:
            return []

        return self._client.embed_documents(list(texts))

    def embed_one(self, text: str) -> list[float]:
        """对单个文本片段或查询语句进行向量化。

        针对单条文本/查询，采用 embed_query 方法能更好地适配部分模型的 Prompt 逻辑。

        Args:
            text: 待嵌入的单条文本字符串。

        Returns:
            代表该文本向量的浮点数列表。
        """
        return self._client.embed_query(text)

    def embed_chunks(self, chunks: Sequence[Chunk]) -> list[list[float]]:
        """提取 Chunk 对象的文本内容并批量生成向量。

        Args:
            chunks: 包含文本内容（content 属性）的 Chunk 领域对象序列。

        Returns:
            浮点数列表的列表，按顺序对应各个 Chunk 的向量表示。
        """
        texts = [chunk.content for chunk in chunks]
        return self.embed(texts)
