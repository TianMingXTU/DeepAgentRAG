# deeprag_coder/config/settings.py
"""配置管理 — 所有环境变量和默认值的单一入口。"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


@dataclass
class LLMConfig:
    """LLM 模型配置。兼容 OpenAI 兼容 API。"""

    model: str = os.getenv("model", "gpt-4o-mini")
    api_key: str = os.getenv("api_key", "")
    base_url: str | None = os.getenv("base_url") or None
    temperature: float = 0.0


@dataclass
class RAGConfig:
    """RAG 管道配置。"""

    # 分块参数
    chunk_max_lines: int = 150
    chunk_overlap_lines: int = 20
    min_chunk_lines: int = 10

    # 嵌入
    embedding_model: str = os.getenv("embedding_model", "Qwen/Qwen3-Embedding-0.6B")
    embedding_base_url: str | None = os.getenv("embedding_base_url") or None
    embedding_api_key: str = os.getenv("embedding_api_key", "")
    embedding_batch_size: int = 50

    # 检索
    top_k: int = 10
    bm25_weight: float = 0.3  # BM25 在混合检索中的权重
    semantic_weight: float = 0.7  # 向量相似度权重

    # 向量库
    vector_db_path: Path = Path("data/vector_store")
    collection_name: str = "deeprag_code"


# 在 RAGConfig 之后追加
@dataclass
class RerankConfig:
    """Rerank 二次精排配置。

    默认走 Cohere 云端 rerank API；base_url 设置后可指向
    任意 Cohere 协议兼容的 /v1/rerank 端点（如 SiliconFlow）。
    """

    enabled: bool = os.getenv("rerank_enabled", "false").lower() == "true"
    provider: str = os.getenv(
        "rerank_provider", "cohere"
    )  # 预留：cohere / nvidia / jina
    model: str = os.getenv("rerank_model", "rerank-multilingual-v3.0")
    top_n: int = int(os.getenv("rerank_top_n", "5"))
    api_key: str = os.getenv("cohere_api_key", "")
    base_url: str | None = os.getenv("rerank_base_url") or None


@dataclass
class SearchConfig:
    """外部搜索配置。"""

    tavily_key: str = os.getenv("tavily_key", "")


@dataclass
class LangSmithConfig:
    """LangSmith 观测配置。"""

    enabled: bool = os.getenv("LANGSMITH_TRACING", "true").lower() == "true"
    endpoint: str = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    api_key: str = os.getenv("LANGSMITH_API_KEY", "")
    project: str = os.getenv("LANGSMITH_PROJECT", "deeprag-coder")

    def configure(self) -> None:
        """注入 LangSmith 环境变量（若未已经设置）。"""
        if self.enabled:
            os.environ.setdefault("LANGSMITH_TRACING", "true")
            os.environ.setdefault("LANGSMITH_ENDPOINT", self.endpoint)
            os.environ.setdefault("LANGSMITH_API_KEY", self.api_key)
            os.environ.setdefault("LANGSMITH_PROJECT", self.project)


@dataclass
class Settings:
    """顶层配置聚合。"""

    llm: LLMConfig = field(default_factory=LLMConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    langsmith: LangSmithConfig = field(default_factory=LangSmithConfig)
    rerank: RerankConfig = field(default_factory=RerankConfig)

    # 仓库路径（运行时动态设置）
    repo_path: Path = Path.cwd()
    data_dir: Path = Path("data")

    verbose: bool = False


# 全局单例
_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.langsmith.configure()
    return _settings


def reset_settings(new: Settings | None = None) -> None:
    global _settings
    _settings = new
