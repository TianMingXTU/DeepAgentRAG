"""code_analyze Tool — 代码深度分析。"""

from pathlib import Path

from langchain_core.tools import tool

from deeprag_coder.rag.pipeline import get_graph, get_pipeline


@tool
def code_analyze(file_path: str, symbol: str = "") -> str:
    """Analyze a code file or function in detail.

    Use this when you need deep understanding of implementation details,
    dependencies, or call chains for a specific file or symbol.

    Args:
        file_path: Path to the code file (relative to repo root).
        symbol: Optional function or class name to focus analysis on.

    Returns:
        Structured analysis with implementation details, dependencies, and suggestions.
    """
    pipe = get_pipeline()
    graph = get_graph()

    lines: list[str] = []

    # 1. RAG search for relevant context
    query = symbol if symbol else Path(file_path).stem
    docs = pipe.search(query, top_k=5)
    file_snippets = [d for d in docs if file_path in d.metadata.get("file_path", "")]
    if file_snippets:
        lines.append(f"## {file_path} 中的相关代码")
        for d in file_snippets:
            lines.append(d.page_content[:500])
    elif docs:
        lines.append(f"## 相关代码片段")
        for d in docs[:3]:
            fp = d.metadata.get("file_path", "?")
            lines.append(f"--- {fp} ---")
            lines.append(d.page_content[:300])

    # 2. Graph query for dependencies
    if symbol and symbol in graph:
        callers = list(graph.predecessors(symbol))
        callees = list(graph.successors(symbol))
        if callers:
            lines.append(f"\n## 调用 '{symbol}' 的符号")
            lines.extend(f"  {c}" for c in callers[:10])
        if callees:
            lines.append(f"\n## '{symbol}' 调用的符号")
            lines.extend(f"  {c}" for c in callees[:10])

    return "\n".join(lines) if lines else f"未找到 {file_path} 的相关信息。"
