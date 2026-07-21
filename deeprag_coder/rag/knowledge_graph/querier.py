"""知识图谱查询器 — 入度/出度/影响面分析。"""

import logging
from typing import Any

import networkx as nx

logger = logging.getLogger(__name__)


class GraphQuerier:
    """对调用关系图执行结构化查询。

    用法:
        >>> querier = GraphQuerier(G)
        >>> querier.callers_of("helper")
        >>> querier.impact_chain("helper", depth=3)
    """

    def __init__(self, graph: nx.DiGraph) -> None:
        self.G = graph

    def callers_of(self, name: str) -> list[dict[str, Any]]:
        """谁调用了指定符号。"""
        if name not in self.G:
            return []
        return [
            {
                "caller": src,
                "type": self.G.edges[src, name].get("type", "calls"),
                "file": self.G.nodes[src].get("file", "?"),
                "line": self.G.nodes[src].get("line", 0),
            }
            for src in self.G.predecessors(name)
            if self.G.edges[src, name].get("type") == "calls"
        ]

    def callees_of(self, name: str) -> list[dict[str, Any]]:
        """指定符号调用了谁。"""
        if name not in self.G:
            return []
        return [
            {
                "callee": dst,
                "type": self.G.edges[name, dst].get("type", "calls"),
                "file": self.G.nodes[dst].get("file", "?"),
                "line": self.G.nodes[dst].get("line", 0),
            }
            for dst in self.G.successors(name)
            if self.G.edges[name, dst].get("type") == "calls"
        ]

    def impact_chain(
        self, name: str, max_depth: int = 3
    ) -> list[list[dict[str, Any]]]:
        """影响面传播：如果修改 name，哪些函数会受影响。

        返回多条路径，每条路径从 name 出发向外传播。
        """
        if name not in self.G:
            return []
        paths: list[list[dict[str, Any]]] = []
        visited: set[str] = set()

        def dfs(current: str, path: list[dict[str, Any]], depth: int) -> None:
            if depth > max_depth:
                return
            visited.add(current)
            callers = self.callers_of(current)
            if not callers:
                paths.append(path)
            for c in callers:
                n = c["caller"]
                if n not in visited:
                    dfs(n, path + [c], depth + 1)

        dfs(name, [], 1)
        return paths

    def summary(self) -> str:
        """图谱统计摘要文本。"""
        total = self.G.number_of_nodes()
        called = len(
            {n for n in self.G.nodes if self.G.out_degree(n) > 0}
        )
        leaf = total - called
        return (
            f"知识图谱统计:\n"
            f"  - 符号总数: {total}\n"
            f"  - 有调用关系的符号: {called}\n"
            f"  - 叶子节点（无出边）: {leaf}\n"
            f"  - 调用边总数: {self.G.number_of_edges()}"
        )