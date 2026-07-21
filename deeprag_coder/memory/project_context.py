"""项目上下文记忆 — CompositeBackend + StoreBackend 持久化配置。"""

from dataclasses import dataclass, field

from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore


@dataclass(frozen=True)
class MemoryContext:
    """运行时上下文，用于 namespace 路由。"""
    user_id: str = "local-user"


def user_namespace(rt):
    """按用户隔离的 namespace。"""
    if rt.server_info and rt.server_info.user:
        return (rt.server_info.user.identity,)
    return ("local-user",)


def agent_namespace(rt):
    """Agent 级 namespace（所有用户共享）。"""
    return ("deeprag-coder",)


def create_memory_backend() -> CompositeBackend:
    """创建混合内存后端：临时 + 持久化。

    - 默认路径 → StateBackend（临时，对话结束后丢失）
    - /memories/ → StoreBackend（跨对话持久化，按用户隔离）

    Returns:
        配置好的 CompositeBackend。
    """
    store = InMemoryStore()
    backend = CompositeBackend(
        default=StateBackend(),
        routes={
            "/memories/": StoreBackend(namespace=user_namespace),
        },
    )
    return backend


def get_store() -> InMemoryStore:
    """获取全局 Store 实例（InMemoryStore 开发用，生产换 PostgresStore）。"""
    return InMemoryStore()
