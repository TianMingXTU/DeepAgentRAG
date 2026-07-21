"""Agent 工厂 — 装配所有 RAG Tool + Subagents + Memory + Permissions 到 Deep Agents。"""

from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend

from deeprag_coder.config.settings import get_settings
from deeprag_coder.agent.prompts import CODE_REPO_EXPERT_PROMPT
from deeprag_coder.agent.subagents import (
    code_analyzer_subagent,
    doc_generator_subagent,
    refactor_subagent,
)
from deeprag_coder.agent.permissions import DEFAULT_PERMISSIONS
from deeprag_coder.memory.project_context import create_memory_backend, get_store, MemoryContext
from deeprag_coder.tools.rag_search import rag_search
from deeprag_coder.tools.rag_ask import rag_ask
from deeprag_coder.tools.graph_query import graph_query
from deeprag_coder.tools.code_analyze import code_analyze
from deeprag_coder.tools.doc_generate import doc_generate


def create_deeprag_agent(repo_path: str | None = None) -> object:
    """创建装配完整的 DeepRAG-Coder Agent。

    Args:
        repo_path: 仓库根路径。为 None 时使用 settings 中的值。

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

    root = repo_path or str(cfg.repo_path)

    tools = [rag_search, rag_ask, graph_query, code_analyze, doc_generate]

    subagents = [code_analyzer_subagent, doc_generator_subagent, refactor_subagent]

    skills = [
        "deeprag_coder/skills/code-review/",
        "deeprag_coder/skills/refactor/",
        "deeprag_coder/skills/doc-gen/",
        "deeprag_coder/skills/bug-hunt/",
    ]

    backend = create_memory_backend()
    store = get_store()

    return create_deep_agent(
        model=llm,
        system_prompt=CODE_REPO_EXPERT_PROMPT,
        tools=tools,
        subagents=subagents,
        skills=skills,
        backend=backend,
        store=store,
        permissions=DEFAULT_PERMISSIONS,
        memory=["/memories/AGENTS.md"],
        context_schema=MemoryContext,
        interrupt_on={
            "write_file": {"allowed_decisions": ["approve", "edit", "reject"]},
            "edit_file": {"allowed_decisions": ["approve", "edit", "reject"]},
        },
    )
