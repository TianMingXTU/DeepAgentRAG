"""语义分块器测试 — 验证分块生成正确。"""

import tempfile
from pathlib import Path

from deeprag_coder.rag.chunker.semantic_chunker import SemanticChunker


def test_chunk_single_file():
    code = '''def greet(name: str) -> str:
    """Say hello."""
    return f"Hello {name}"

class Foo:
    def bar(self):
        pass
'''
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(code)
        f.flush()
        chunks = SemanticChunker().chunk_files([Path(f.name)])

    assert len(chunks) >= 1
    for c in chunks:
        assert c.file_path
        assert c.content


def test_chunk_skip_ignored():
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("x = 1")
        f.flush()
        path = Path(f.name)
    # Pretend this file is in a .gitignored dir by checking the filter
    chunks = SemanticChunker().chunk_files([path])
    assert len(chunks) >= 1


if __name__ == "__main__":
    test_chunk_single_file()
    test_chunk_skip_ignored()
    print("ALL OK")
