"""Agent 工厂 — 装配所有 Tool + Subagent + Permission + Memory 到 Deep Agents。"""

from typing import Literal

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
from deeprag_coder.agent.permissions import (
    build_deepagents_permissions,
    DEFAULT_RULES,
)
from deeprag_coder.memory.project_context import (
    create_memory_backend,
    get_store,
    MemoryContext,
)
from deeprag_coder.tools.rag_search import rag_search
from deeprag_coder.tools.rag_ask import rag_ask
from deeprag_coder.tools.graph_query import graph_query
from deeprag_coder.tools.code_analyze import code_analyze
from deeprag_coder.tools.doc_generate import doc_generate
from deeprag_coder.tools.lsp_tool import lsp_goto_def, lsp_references


def create_deeprag_agent(
    repo_path: str | None = None,
    mode: Literal["plan", "build"] = "build",
) -> object:
    """创建装配完整的 DeepRAG-Coder Agent。

    Args:
        repo_path: 仓库根路径。为 None 时使用 settings 中的值。
        mode: "plan" 只读分析模式（零中断 + 只读权限）
              "build" 读写执行模式（写操作需审批）。

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

    # 统一工具集：RAG + KG + LSP
    tools = [
        rag_search,
        rag_ask,
        graph_query,
        code_analyze,
        doc_generate,
        lsp_goto_def,
        lsp_references,
    ]

    # 子智能体：name 字段必须存在，供 @mention / Task tool 识别
    subagents = [
        code_analyzer_subagent,
        doc_generator_subagent,
        refactor_subagent,
    ]

    skills = [
        "deeprag_coder/skills/code-review/",
        "deeprag_coder/skills/refactor/",
        "deeprag_coder/skills/doc-gen/",
        "deeprag_coder/skills/bug-hunt/",
    ]

    # 权限矩阵（按 mode 区分）
    permissions = build_deepagents_permissions(DEFAULT_RULES, mode=mode)

    # Plan 模式：零中断 + 只读 FilesystemBackend
    # Build 模式：写操作需 human-in-the-loop 审批
    interrupt_on = {}
    backend = FilesystemBackend(root_dir=root, virtual_mode=True)

    if mode == "build":
        interrupt_on = {
            "write_file": {"allowed_decisions": ["approve", "edit", "reject"]},
            "edit_file": {"allowed_decisions": ["approve", "edit", "reject"]},
        }

    store = get_store()

    return create_deep_agent(
        model=llm,
        system_prompt=CODE_REPO_EXPERT_PROMPT,
        tools=tools,
        subagents=subagents,
        skills=skills,
        backend=backend,
        store=store,
        permissions=permissions,
        memory=["/memories/AGENTS.md"],
        context_schema=MemoryContext,
        interrupt_on=interrupt_on,
    )
