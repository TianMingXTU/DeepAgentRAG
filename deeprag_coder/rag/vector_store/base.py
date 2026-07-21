"""向量存储抽象接口 — 便于未来换 Qdrant / Milvus。"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence


@dataclass
class VectorRecord:
    id: str
    vector: List[float]
    text: str
    metadata: dict


class VectorStore(ABC):
    @abstractmethod
    def add(self, records: Sequence[VectorRecord]) -> None: ...

    @abstractmethod
    def search(
        self,
        query_vector: List[float],
        top_k: int,
        filter_: dict | None = None,
    ) -> List[VectorRecord]: ...

    @abstractmethod
    def delete(self, ids: Sequence[str]) -> None: ...

    @abstractmethod
    def persist(self) -> None: ...

    @abstractmethod
    def count(self) -> int: ...
