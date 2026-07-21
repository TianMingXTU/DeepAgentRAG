"""doc_generate Tool — 代码文档生成。"""

from pathlib import Path

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from deeprag_coder.config.settings import get_settings
from deeprag_coder.rag.pipeline import get_pipeline


@tool
def doc_generate(file_path: str, symbol: str = "") -> str:
    """Generate documentation for a code symbol (function, class, module).

    Use this when the user wants to add or update docstrings, generate API docs,
    or create inline documentation for code.

    Args:
        file_path: Path to the code file (relative to repo root).
        symbol: Optional specific function or class name to document.
                Leave empty to document the entire file.

    Returns:
        Generated documentation following the project's style.
    """
    pipe = get_pipeline()
    cfg = get_settings()

    query = symbol if symbol else Path(file_path).stem
    docs = pipe.search(query, top_k=3)

    context = "\n---\n".join(
        f"{d.metadata.get('file_path', '?')}:\n{d.page_content}" for d in docs
    )

    llm = ChatOpenAI(
        model=cfg.llm.model,
        api_key=cfg.llm.api_key,
        base_url=cfg.llm.base_url,
        temperature=0,
    )

    prompt = (
        "Generate documentation for the given code symbol. "
        "Follow Chinese Google-style docstring format (Args: / Returns: / Raises:).\n\n"
        f"File: {file_path}\n"
        f"Symbol: {symbol or '(entire file)'}\n\n"
        f"## Context\n{context}"
    )
    return llm.invoke(prompt).content
