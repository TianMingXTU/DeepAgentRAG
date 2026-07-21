"""Agent 工厂 — 装配所有 RAG Tool 到 Deep Agents。"""

from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent, FilesystemPermission
from deepagents.backends import FilesystemBackend

from deeprag_coder.config.settings import get_settings
from deeprag_coder.agent.prompts import CODE_REPO_EXPERT_PROMPT
from deeprag_coder.tools.rag_search import rag_search
from deeprag_coder.tools.rag_ask import rag_ask
from deeprag_coder.tools.graph_query import graph_query


def create_deeprag_agent():
    """创建装配完成的 DeepRAG-Coder Agent。

    Returns:
        Deep Agents 可调用实例。
    """
    cfg = get_settings()
    llm = ChatOpenAI(
        model=cfg.llm.model,
        api_key=cfg.llm.api_key,
        base_url=cfg.llm.base_url,
        temperature=0,
    )
    return create_deep_agent(
        model=llm,
        system_prompt=CODE_REPO_EXPERT_PROMPT,
        backend=FilesystemBackend(root_dir=".", virtual_mode=True),
        tools=[rag_search, rag_ask,graph_query],
        permissions=[
            FilesystemPermission(
                operations=["write"], paths=["/deeprag_coder/**"], mode="deny"
            )
        ],
    )
