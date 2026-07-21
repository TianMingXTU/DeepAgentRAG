"""混合检索器测试 — 验证 BM25 + 向量检索可初始化。"""

from pathlib import Path

from deeprag_coder.rag.chunker.semantic_chunker import Chunk
from deeprag_coder.rag.retriever.hybrid_retriever import HybridRetriever
from deeprag_coder.rag.vector_store.chroma_store import ChromaStore


def test_hybrid_retriever_init():
    store = ChromaStore()
    assert store is not None
    hybrid = HybridRetriever(chroma_store=store)
    assert hybrid is not None


def test_bm25_fit_and_search():
    store = ChromaStore()
    hybrid = HybridRetriever(chroma_store=store)
    chunks = [
        Chunk(chunk_id="c1", file_path=Path("a.py"), symbol_names=[], start_line=1, end_line=1, content="def foo(): pass"),
        Chunk(chunk_id="c2", file_path=Path("b.py"), symbol_names=[], start_line=1, end_line=1, content="def bar(): return 42"),
    ]
    hybrid.fit_bm25(chunks)
    results = hybrid.invoke("foo")
    assert len(results) > 0


if __name__ == "__main__":
    test_hybrid_retriever_init()
    test_bm25_fit_and_search()
    print("ALL OK")
