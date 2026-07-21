"""rag_search Tool — 语义搜索代码仓库。"""

from langchain_core.tools import tool

from deeprag_coder.rag.pipeline import get_pipeline


@tool
def rag_search(query: str, top_k: int = 10) -> list[dict]:
    """Search the codebase for relevant code snippets matching the query.

    Use this when you need to find specific code implementations, APIs,
    or patterns in the project. Returns code chunks with file paths.

    Args:
        query: Natural language or code search query.
        top_k: Maximum number of results to return.

    Returns:
        List of dicts with 'file_path', 'content', and 'score'.
    """
    pipe = get_pipeline()
    docs = pipe.search(query, top_k=top_k)
    return [
        {
            "file_path": d.metadata.get("file_path", "?"),
            "content": d.page_content,
            "score": d.metadata.get("rerank_score", 0),
        }
        for d in docs
    ]
