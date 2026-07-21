"""上下文组装器测试。"""

from langchain_core.documents import Document

from deeprag_coder.rag.context_assembler import assemble_context


def test_assemble_basic():
    docs = [
        Document(page_content="def foo(): pass", metadata={"file_path": "a.py", "start_line": 1}),
        Document(page_content="class Bar: pass", metadata={"file_path": "b.py", "start_line": 5}),
    ]
    result = assemble_context("how does foo work?", docs, repo_map="## Project\n- a.py")
    assert "## Project Structure" in result
    assert "## Relevant Code" in result
    assert "## Question" in result
    assert "how does foo work?" in result


def test_assemble_empty_chunks():
    result = assemble_context("test", [], repo_map="")
    assert "## Relevant Code" not in result
    assert "## Question" in result


if __name__ == "__main__":
    test_assemble_basic()
    test_assemble_empty_chunks()
    print("ALL OK")
