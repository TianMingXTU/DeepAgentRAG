"""配置管理 — 默认值工厂 + 分层加载入口。

保留默认值为 fallback，实际运行时由 config/loader.py 执行
Defaults → Global JSON → Project JSON → Env 四层合并。
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


@dataclass
class LLMConfig:
    """LLM 模型配置。兼容 OpenAI 兼容 API。"""

    model: str = os.environ.get("DEEPAGENT_MODEL", os.environ.get("model", "gpt-4o-mini"))
    api_key: str = os.environ.get("DEEPAGENT_API_KEY", os.environ.get("api_key", ""))
    base_url: str | None = os.environ.get("DEEPAGENT_BASE_URL", os.environ.get("base_url", None))
    temperature: float = float(os.environ.get("DEEPAGENT_TEMPERATURE", "0.0"))


@dataclass
class RAGConfig:
    """RAG 管道配置。"""

    chunk_max_lines: int = int(os.environ.get("DEEPAGENT_CHUNK_MAX_LINES", "150"))
    chunk_overlap_lines: int = int(os.environ.get("DEEPAGENT_CHUNK_OVERLAP", "20"))
    min_chunk_lines: int = int(os.environ.get("DEEPAGENT_MIN_CHUNK_LINES", "10"))
    embedding_model: str = os.environ.get("DEEPAGENT_EMBEDDING_MODEL", os.environ.get("embedding_model", "Qwen/Qwen3-Embedding-0.6B"))
    embedding_base_url: str | None = os.environ.get("DEEPAGENT_EMBEDDING_BASE_URL", os.environ.get("embedding_base_url", None))
    embedding_api_key: str = os.environ.get("DEEPAGENT_EMBEDDING_API_KEY", os.environ.get("embedding_api_key", ""))
    embedding_batch_size: int = int(os.environ.get("DEEPAGENT_EMBEDDING_BATCH_SIZE", "50"))
    top_k: int = 10
    bm25_weight: float = 0.3
    semantic_weight: float = 0.7
    vector_db_path: Path = Path("data/vector_store")
    collection_name: str = "deeprag_code"


@dataclass
class RerankConfig:
    """Rerank 二次精排配置。"""

    enabled: bool = False
    provider: str = "cohere"
    model: str = "rerank-multilingual-v3.0"
    top_n: int = 5
    api_key: str = ""
    base_url: str | None = None


@dataclass
class SearchConfig:
    """外部搜索配置。"""

    tavily_key: str = ""


@dataclass
class LangSmithConfig:
    """LangSmith 观测配置。"""

    enabled: bool = True
    endpoint: str = "https://api.smith.langchain.com"
    api_key: str = ""
    project: str = "deeprag-coder"

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
    repo_path: Path = Path.cwd()
    data_dir: Path = Path("data")
    verbose: bool = False


_settings: Settings | None = None


def get_settings() -> Settings:
    """获取配置（首次调用时从 loader 加载）。"""
    global _settings
    if _settings is None:
        # ponytail: lazy import to avoid circular dep
        from deeprag_coder.config.loader import load_config
        _settings = load_config()
        _settings.langsmith.configure()
    return _settings


def reset_settings(new: Settings | None = None) -> None:
    global _settings
    _settings = new
