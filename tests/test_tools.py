"""Tool 可调用性测试 — 验证工具签名和 docstring 符合 Deep Agents 要求。"""

from deeprag_coder.tools.rag_search import rag_search
from deeprag_coder.tools.rag_ask import rag_ask
from deeprag_coder.tools.graph_query import graph_query
from deeprag_coder.tools.code_analyze import code_analyze
from deeprag_coder.tools.doc_generate import doc_generate


def _check_tool(tool, name):
    assert tool.name == name, f"expected {name}, got {tool.name}"
    assert tool.description, f"{name}: empty description"
    # All args must have type annotations
    for arg_name, arg_type in tool.args.items():
        if arg_name == "tool_call_id":
            continue
        assert arg_type["type"] is not None, f"{name}.{arg_name}: missing type"


def test_rag_search_tool():
    _check_tool(rag_search, "rag_search")


def test_rag_ask_tool():
    _check_tool(rag_ask, "rag_ask")


def test_graph_query_tool():
    _check_tool(graph_query, "graph_query")


def test_code_analyze_tool():
    _check_tool(code_analyze, "code_analyze")


def test_doc_generate_tool():
    _check_tool(doc_generate, "doc_generate")


def test_all_tools_have_docstrings():
    tools = [rag_search, rag_ask, graph_query, code_analyze, doc_generate]
    for t in tools:
        assert t.description, f"{t.name}: missing docstring/description"


if __name__ == "__main__":
    test_rag_search_tool()
    test_rag_ask_tool()
    test_graph_query_tool()
    test_code_analyze_tool()
    test_doc_generate_tool()
    test_all_tools_have_docstrings()
    print("ALL OK")
