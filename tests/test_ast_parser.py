"""AST 解析器测试 — 验证分块完整性。"""

import tempfile
from pathlib import Path

from deeprag_coder.rag.chunker.ast_parser import ASTParser


def test_parse_python_class_and_function():
    code = '''import os

class Calculator:
    """A simple calculator."""

    def add(self, a: int, b: int) -> int:
        return a + b

    def multiply(self, a: int, b: int) -> int:
        return a * b

def main():
    calc = Calculator()
    print(calc.add(1, 2))
'''
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(code)
        f.flush()
        result = ASTParser().parse(Path(f.name))

    assert result.error is None
    # Calculator class + add method + multiply method + main function = 4 blocks
    assert len(result.blocks) >= 4
    names = [b.symbol_name for b in result.blocks if b.symbol_name]
    assert "Calculator" in names
    assert "add" in names
    assert "multiply" in names
    assert "main" in names


def test_parse_empty_file():
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write("")
        f.flush()
        result = ASTParser().parse(Path(f.name))

    assert result.error is None or "no source" in (result.error or "").lower()


def test_parse_unknown_extension():
    with tempfile.NamedTemporaryFile(suffix=".xyz", mode="w", delete=False) as f:
        f.write("hello world")
        f.flush()
        result = ASTParser().parse(Path(f.name))

    assert result.error is not None


if __name__ == "__main__":
    test_parse_python_class_and_function()
    test_parse_empty_file()
    test_parse_unknown_extension()
    print("ALL OK")
