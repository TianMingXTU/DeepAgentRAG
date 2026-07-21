"""基于 ChromaDB 的向量存储实现模块。

提供嵌入式、零配置的本地持久化向量数据库接入能力。
"""

from pathlib import Path
from typing import Sequence

import chromadb
from chromadb.config import Settings as ChromaSettings

from deeprag_coder.config.settings import get_settings
from deeprag_coder.rag.vector_store.base import VectorRecord, VectorStore


class ChromaStore(VectorStore):
    """基于 ChromaDB 实现的向量存储客户端。

    示例:
        >>> store = ChromaStore()
        >>> record = VectorRecord(
        ...     id="1", vector=[0.1] * 1536, text="def foo(): pass", metadata={}
        ... )
        >>> store.add([record])
        >>> results = store.search([0.1] * 1536, top_k=5)
    """

    def __init__(
        self,
        persist_dir: Path | None = None,
        collection_name: str | None = None,
    ) -> None:
        """初始化 ChromaStore 实例。

        Args:
            persist_dir: 数据持久化存储目录Path对象。若未提供则从全局配置读取。
            collection_name: 集合名称。若未提供则从全局配置读取。
        """
        cfg = get_settings().rag
        self._persist_dir = persist_dir or cfg.vector_db_path
        self._collection_name = collection_name or cfg.collection_name

        # 确保持久化目录存在
        self._persist_dir.mkdir(parents=True, exist_ok=True)

        # 初始化持久化客户端（禁用匿名数据收集）
        self._client = chromadb.PersistentClient(
            path=str(self._persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # 获取或创建 Collection，指定使用余弦相似度计算算法
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, records: Sequence[VectorRecord]) -> None:
        """批量写入向量记录至数据库。

        Args:
            records: 向量记录（VectorRecord）序列。
        """
        if not records:
            return

        self._collection.add(
            ids=[record.id for record in records],
            embeddings=[record.vector for record in records],
            documents=[record.text for record in records],
            metadatas=[record.metadata for record in records],
        )

    def add_from_chunks(self, chunks, vectors) -> None:
        """将分块及其向量打包为 VectorRecord 后写入向量数据库。

        Args:
            chunks: 代码/文本分块对象序列。
            vectors: 对应 chunks 的向量嵌入列表。
        """
        records = []
        for chunk, vector in zip(chunks, vectors):
            record = VectorRecord(
                id=getattr(
                    chunk,
                    "id",
                    f"{getattr(chunk, 'file_path', 'doc')}:{getattr(chunk, 'start_line', 0)}",
                ),
                vector=vector,
                text=getattr(chunk, "content", getattr(chunk, "text", "")),
                metadata=getattr(chunk, "metadata", {}),
            )
            records.append(record)

        self.add(records)

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filter_: dict | None = None,
    ) -> list[VectorRecord]:
        """根据查询向量检索最为相似的向量记录。

        Args:
            query_vector: 查询的高维向量列表。
            top_k: 期望返回的最相似结果数量。
            filter_: 元数据过滤条件字典（等同于 ChromaDB 的 where 参数）。

        Returns:
            检索到的 VectorRecord 列表。
        """
        # 执行向量检索
        results = self._collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=filter_,
            include=["documents", "metadatas", "distances"],
        )

        # 校验检索结果合法性
        ids_batch = results.get("ids")
        if not ids_batch or not ids_batch[0]:
            return []

        # 格式化输出为统一的 VectorRecord 领域模型
        out_records: list[VectorRecord] = []
        for i, record_id in enumerate(ids_batch[0]):
            text = results["documents"][0][i] if results.get("documents") else ""
            metadata = results["metadatas"][0][i] if results.get("metadatas") else {}

            out_records.append(
                VectorRecord(
                    id=record_id,
                    vector=[],  # Chroma 默认不返回原始向量以节省 IO/内存
                    text=text,
                    metadata=metadata or {},
                )
            )

        return out_records

    def delete(self, ids: Sequence[str]) -> None:
        """根据主键 ID 批量删除数据。

        Args:
            ids: 待删除记录的唯一 ID 序列。
        """
        if ids:
            self._collection.delete(ids=list(ids))

    def persist(self) -> None:
        """持久化存储方法。

        注意:
            chromadb.PersistentClient 会自动将变更同步刷入磁盘。
            保留此方法仅为满足 VectorStore 基类抽象接口的约定。
        """
        # 新版 ChromaDB PersistentClient 采用实时持久化，无需手动刷盘
        pass

    def count(self) -> int:
        """获取当前 Collection 中的数据总条数。

        Returns:
            记录总数。
        """
        return self._collection.count()
