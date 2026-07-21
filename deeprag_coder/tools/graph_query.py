"""graph_query Tool — 知识图谱调用链查询。"""

from langchain_core.tools import tool

from deeprag_coder.rag.knowledge_graph.querier import GraphQuerier
from deeprag_coder.rag.pipeline import get_graph


@tool
def graph_query(symbol: str, mode: str = "impact") -> str:
    """Query the code knowledge graph for symbol dependencies.

    Use this when you need to understand what functions call a given symbol,
    what a symbol calls, or trace the full impact chain of a change.

    Args:
        symbol: The function or class name to query.
        mode: Query type - "impact" (who calls this symbol),
              "depends" (what this symbol calls),
              "chain" (full impact propagation chain).

    Returns:
        Formatted text showing call relationships.
    """
    q = GraphQuerier(get_graph())
    if mode == "impact":
        results = q.callers_of(symbol)
        if not results:
            return f"'{symbol}' 没有被其他符号调用。"
        lines = [f"调用 '{symbol}' 的符号:"]
        for r in results:
            lines.append(f"  {r['caller']} ({r['file']}:{r['line']})")
        return "\n".join(lines)

    if mode == "depends":
        results = q.callees_of(symbol)
        if not results:
            return f"'{symbol}' 没有调用其他符号。"
        lines = [f"'{symbol}' 调用的符号:"]
        for r in results:
            lines.append(f"  {r['callee']} ({r['file']}:{r['line']})")
        return "\n".join(lines)

    if mode == "chain":
        chains = q.impact_chain(symbol)
        if not chains:
            return f"'{symbol}' 没有影响链。"
        lines = [f"修改 '{symbol}' 的影响传播链:"]
        for i, chain in enumerate(chains, 1):
            path = " → ".join(c["caller"] for c in chain)
            lines.append(f"  路径 {i}: {symbol} → {path}")
        return "\n".join(lines)

    return f"未知查询模式: {mode}，可选: impact / depends / chain"
