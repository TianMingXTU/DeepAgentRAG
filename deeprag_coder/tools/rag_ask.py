"""rag_ask Tool — 基于 RAG 上下文的代码问答。"""

from langchain_core.tools import tool

from deeprag_coder.rag.pipeline import get_pipeline


@tool
def rag_ask(question: str) -> str:
    """Answer a question about the codebase using RAG.

    Use this when the user asks a question about how code works,
    where something is implemented, or why something behaves a certain way.
    The tool searches the codebase and generates an answer with citations.

    Args:
        question: The user's question about the codebase.

    Returns:
        Answer with code references and file path citations.
    """
    pipe = get_pipeline()
    return pipe.ask(question)
