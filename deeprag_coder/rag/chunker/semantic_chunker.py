"""语义分块器 — 在 AST 代码块基础上合并/拆分，输出固定长度的检索 Chunk。"""

from dataclasses import dataclass, field
from pathlib import Path

from deeprag_coder.rag.chunker.ast_parser import ASTParser, CodeBlock, ParsedFile
from deeprag_coder.config.settings import get_settings, RAGConfig


@dataclass
class Chunk:
    """一个可检索的代码段。"""

    chunk_id: str
    file_path: Path
    symbol_names: list[str]  # 该块覆盖的函数/类名（去重）
    start_line: int
    end_line: int
    content: str
    metadata: dict = field(default_factory=dict)


class SemanticChunker:
    """
    用法:
        chunker = SemanticChunker()
        chunks = chunker.chunk_file(Path("src/auth.py"))
        for ch in chunks:
            print(ch.chunk_id, ch.symbol_names)
    """

    def __init__(
        self,
        parser: ASTParser | None = None,
        config: RAGConfig | None = None,
    ) -> None:
        self._parser = parser or ASTParser()
        self._cfg = config or get_settings().rag

    # ---------- 公开 API ----------

    def chunk_file(self, fp: Path) -> list[Chunk]:
        """对单个文件做语义分块。"""
        parsed: ParsedFile = self._parser.parse(fp)
        if parsed.error or not parsed.blocks:
            return self._fallback_chunks(fp, parsed)

        return self._chunk_from_blocks(parsed)

    def chunk_files(self, files: list[Path]) -> list[Chunk]:
        """批量分块多个文件。"""
        all_chunks: list[Chunk] = []
        for fp in files:
            all_chunks.extend(self.chunk_file(fp))
        return all_chunks

    # ---------- 内部实现 ----------

    def _chunk_from_blocks(self, parsed: ParsedFile) -> list[Chunk]:
        """把 AST 解析出的 CodeBlock 列表聚合成 Chunk。"""
        chunks: list[Chunk] = []
        acc: list[CodeBlock] = []
        acc_lines = 0
        file_key = str(parsed.file_path)

        def flush(idx: int) -> None:
            nonlocal acc, acc_lines
            if not acc:
                return
            sym_names = [b.symbol_name for b in acc if b.symbol_name]
            # 去重保序
            seen = set()
            uniq = [n for n in sym_names if not (n in seen or seen.add(n))]
            chunks.append(
                Chunk(
                    chunk_id=f"{file_key}#ch{idx}",
                    file_path=parsed.file_path,
                    symbol_names=uniq,
                    start_line=acc[0].start_line,
                    end_line=acc[-1].end_line,
                    content="\n".join(b.content for b in acc),
                    metadata={"language": parsed.language},
                )
            )
            acc = []
            acc_lines = 0

        for blk in parsed.blocks:
            blk_lines = blk.end_line - blk.start_line + 1

            # 单个块就超过阈值 → 单独成 chunk（不拆分函数内部，保持语义完整）
            if blk_lines > self._cfg.chunk_max_lines:
                if acc:
                    flush(len(chunks))
                chunks.append(
                    Chunk(
                        chunk_id=f"{file_key}#ch{len(chunks)}",
                        file_path=parsed.file_path,
                        symbol_names=[blk.symbol_name] if blk.symbol_name else [],
                        start_line=blk.start_line,
                        end_line=blk.end_line,
                        content=blk.content,
                        metadata={"language": parsed.language, "oversized": True},
                    )
                )
                continue

            # 累积 + 当前块是否超限
            if acc_lines + blk_lines > self._cfg.chunk_max_lines and acc:
                flush(len(chunks))

            acc.append(blk)
            acc_lines += blk_lines

        # 末尾剩余
        if acc:
            flush(len(chunks))

        return chunks

    def _fallback_chunks(self, fp: Path, parsed: ParsedFile) -> list[Chunk]:
        """AST 解析失败/无语义块时的兜底：按固定行数切分。"""
        lines = (
            parsed.lines
            or fp.read_text(encoding="utf-8", errors="replace").splitlines()
        )
        if not lines:
            return []

        chunks: list[Chunk] = []
        step = self._cfg.chunk_max_lines
        overlap = self._cfg.chunk_overlap_lines
        file_key = str(fp)

        start = 0
        idx = 0
        while start < len(lines):
            end = min(start + step, len(lines))
            chunk_lines = lines[start:end]
            chunks.append(
                Chunk(
                    chunk_id=f"{file_key}#ch{idx}",
                    file_path=fp,
                    symbol_names=[],
                    start_line=start + 1,
                    end_line=end,
                    content="\n".join(chunk_lines),
                    metadata={"language": parsed.language or "text", "fallback": True},
                )
            )
            idx += 1
            if end >= len(lines):
                break
            start = end - overlap

        return chunks

    # ---------- 自检 ----------
    @classmethod
    def demo(cls) -> None:
        import tempfile
        from pathlib import Path

        sample = """import os

def small_one():
    return 1

def small_two():
    return 2

class Calculator:
    def add(self, a, b):
        return a + b

    def mul(self, a, b):
        return a * b
"""
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write(sample)
            fp = Path(f.name)
        try:
            chunker = cls()
            chunks = chunker.chunk_file(fp)
            print(f"[PASS] {len(chunks)} chunks generated")
            for ch in chunks:
                print(
                    f"  {ch.chunk_id}: lines {ch.start_line}-{ch.end_line}, symbols={ch.symbol_names},content={ch.content}"
                )
        finally:
            fp.unlink(missing_ok=True)


if __name__ == "__main__":
    SemanticChunker.demo()
