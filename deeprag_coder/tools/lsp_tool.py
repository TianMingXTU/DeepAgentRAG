"""LSP 工具 — 符号定义跳转 + 引用查找（优先 pyright，回退 tree-sitter）。"""

import json
import subprocess
from pathlib import Path

from langchain_core.tools import tool


def _find_pyright() -> str | None:
    """检查 pyright 是否可用。"""
    for cmd in ("pyright", "pyright-python"):
        try:
            subprocess.run([cmd, "--version"], capture_output=True, timeout=5)
            return cmd
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    return None


def _pyright_goto_def(symbol: str, file: str) -> dict | None:
    """用 pyright --outputjson 获取符号定义位置。"""
    cmd = _find_pyright()
    if not cmd:
        return None
    try:
        result = subprocess.run(
            [cmd, "--outputjson", file],
            capture_output=True, text=True, timeout=30,
        )
        data = json.loads(result.stdout)
        for diag in data.get("diagnostics", []):
            if symbol in diag.get("message", "") and diag.get("severity") == "information":
                return {
                    "file": diag.get("file", file),
                    "line": diag.get("range", {}).get("start", {}).get("line", 0) + 1,
                    "column": diag.get("range", {}).get("start", {}).get("column", 0) + 1,
                }
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        pass
    return None


def _fallback_search(symbol: str, file: str) -> list[dict]:
    """回退策略：tree-sitter / grep 搜索符号。"""
    fp = Path(file)
    if not fp.exists():
        return []
    results = []
    try:
        lines = fp.read_text(encoding="utf-8", errors="replace").splitlines()
        for i, line in enumerate(lines, 1):
            if f"def {symbol}" in line or f"class {symbol}" in line:
                results.append({"file": file, "line": i, "column": line.index(symbol) + 1})
    except OSError:
        pass
    return results


@tool
def lsp_goto_def(symbol: str, file: str) -> dict:
    """Go to definition — find where a symbol is defined.

    Uses pyright when available, falls back to grep-based search.

    Args:
        symbol: The function or class name to locate.
        file: The file path to search in.

    Returns:
        Dict with 'file', 'line', 'column' keys, or error message.
    """
    result = _pyright_goto_def(symbol, file)
    if result:
        return result
    fallback = _fallback_search(symbol, file)
    if fallback:
        return fallback[0]
    return {"error": f"Could not find definition of '{symbol}' in {file}"}


@tool
def lsp_references(symbol: str, file: str) -> list[dict]:
    """Find all references to a symbol in a file.

    Args:
        symbol: The function or class name to find references for.
        file: The file path to search in.

    Returns:
        List of dicts with 'file', 'line', 'column' keys.
    """
    fp = Path(file)
    if not fp.exists():
        return [{"error": f"File not found: {file}"}]
    results = []
    try:
        lines = fp.read_text(encoding="utf-8", errors="replace").splitlines()
        for i, line in enumerate(lines, 1):
            # Skip definition line itself
            if f"def {symbol}" in line or f"class {symbol}" in line:
                continue
            if symbol in line:
                results.append({"file": file, "line": i, "column": line.index(symbol) + 1})
    except OSError:
        pass
    return results
