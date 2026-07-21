"""Repo Map — 快速生成项目文件树和关键符号摘要的轻量文本表示。

用于 Context Assembler，给 LLM 提供项目全局结构视图。
"""

import logging
from pathlib import Path

from deeprag_coder.rag.chunker.ast_parser import ASTParser

logger = logging.getLogger(__name__)

IGNORE_DIRS = frozenset(
    {
        ".git",
        ".venv",
        "__pycache__",
        "node_modules",
        ".tox",
        ".idea",
        ".vscode",
        "dist",
        "build",
        ".egg-info",
        ".mypy_cache",
    }
)
CODE_EXTENSIONS = frozenset(
    {
        ".py",
        ".ts",
        ".js",
        ".go",
        ".java",
        ".rs",
        ".c",
        ".h",
        ".cpp",
        ".rb",
        ".cs",
        ".swift",
        ".kt",
    }
)


def generate_repo_map(repo_root: Path, max_files: int = 50) -> str:
    """生成仓库文件树 + 关键符号摘要。

    逐文件扫描代码文件，提取每个文件中的类/函数定义，
    最终输出为轻量文本，供 LLM 理解项目结构。

    Args:
        repo_root: 仓库根目录路径。
        max_files: 最多扫描的文件数（防止大仓库爆炸）。

    Returns:
        文本格式的仓库地图，空仓库返回提示信息。
    """
    parser = ASTParser()
    lines: list[str] = []
    file_count = 0

    for fp in sorted(repo_root.rglob("*")):
        if not fp.is_file():
            continue
        rel = fp.relative_to(repo_root)
        if any(part.startswith(".") for part in rel.parts):
            continue
        if fp.suffix not in CODE_EXTENSIONS:
            continue

        parsed = parser.parse(fp)
        symbols: list[str] = []
        if not parsed.error:
            for blk in parsed.blocks:
                if blk.symbol_name:
                    kind = "class" if "class" in blk.node_type else "def"
                    symbols.append(f"  {kind} {blk.symbol_name}")

        lines.append(f"📄 {rel}")
        lines.extend(symbols)
        file_count += 1
        if file_count >= max_files:
            lines.append("... (truncated, max_files reached)")
            break

    return "\n".join(lines) if lines else "(empty or no parseable files)"
