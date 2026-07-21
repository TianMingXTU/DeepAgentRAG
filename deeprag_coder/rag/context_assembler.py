"""上下文组装器 — 将检索结果组装为结构化 Prompt。

控制 Token 预算，按优先级依次填充：repo_map → chunks(从高到低) → instruction → query。
超预算时从最低相关性的 chunk 开始丢弃。
"""

import logging
from pathlib import Path
from typing import Sequence

from langchain_core.documents import Document

from deeprag_coder.config.settings import get_settings
from deeprag_coder.utils.repo_map import generate_repo_map

logger = logging.getLogger(__name__)

_CHARS_PER_TOKEN = 3


def _estimate_tokens(text: str) -> int:
    return len(text) // _CHARS_PER_TOKEN


def _fmt_chunk(doc: Document, idx: int) -> str:
    """将单个 Document 格式化为带溯源信息的代码块。"""
    path = doc.metadata.get("file_path", doc.metadata.get("source", "?"))
    lines = ""
    if "start_line" in doc.metadata:
        end = doc.metadata.get("end_line", "")
        lines = f":{doc.metadata['start_line']}-{end}"
    score = doc.metadata.get("rerank_score", doc.metadata.get("relevance_score", ""))
    score_str = f" [score={score:.2f}]" if score != "" else ""
    return f"[{idx}] {path}{lines}{score_str}\n```\n{doc.page_content}\n```"


def assemble_context(
    query: str,
    chunks: Sequence[Document],
    repo_map: str = "",
    max_tokens: int = 6000,
    reserve_ratio: float = 0.3,
) -> str:
    """将查询和检索结果组装为结构化 Prompt。

    Args:
        query: 用户原始问题。
        chunks: 已按相关性降序排列的检索结果列表。
        repo_map: 项目文件树 + 符号摘要文本。
        max_tokens: 上下文最大 Token 预算（不含 answer 预留）。
        reserve_ratio: 为 LLM 回答预留的 Token 比例。

    Returns:
        格式化后的 Prompt 字符串。
    """
    budget = int(max_tokens * (1 - reserve_ratio))
    used = 0
    parts: list[str] = []

    if repo_map:
        t = _estimate_tokens(repo_map)
        if used + t <= budget:
            parts.append(f"## Project Structure\n{repo_map}")
            used += t

    remaining = budget - used
    chunk_lines: list[str] = []
    for i, doc in enumerate(chunks, 1):
        block = _fmt_chunk(doc, i)
        t = _estimate_tokens(block)
        if remaining - t < 0:
            logger.info(
                "Token budget exhausted, dropped %d lower-priority chunks",
                len(chunks) - i + 1,
            )
            break
        chunk_lines.append(block)
        remaining -= t

    if chunk_lines:
        parts.append("## Relevant Code\n" + "\n---\n".join(chunk_lines))

    parts.append(
        "## Instructions\n"
        "Answer the user's question based on the project structure and code above.\n"
        "Cite file paths and line numbers when referencing code.\n"
        "If the context is insufficient, state what is missing.\n"
    )
    parts.append(f"## Question\n{query}")

    return "\n\n".join(parts)
