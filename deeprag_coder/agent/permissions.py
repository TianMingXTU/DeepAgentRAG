"""细粒度权限规则 — 扩展 Deep Agents FilesystemPermission。"""

from dataclasses import dataclass
from typing import Literal

from deepagents import FilesystemPermission


@dataclass(frozen=True)
class PermissionRule:
    """细粒度权限规则，覆盖所有操作类别。

    Args:
        tool: 操作类型（read / write 最终映射到 FilesystemPermission，
              bash/task/lsp 等由框架内部处理）。
        pattern: glob pattern 路径匹配。
        action: allow=允许, ask=审批中断, deny=拒绝。
    """
    tool: str
    pattern: str
    action: Literal["allow", "deny", "ask"]


# 默认规则：保护自身源码 + 敏感文件，其余默认 allow（OpenCode 风格）
DEFAULT_RULES: tuple[PermissionRule, ...] = (
    PermissionRule("write", "/deeprag_coder/**", "deny"),
    PermissionRule("write", "/.env", "deny"),
    PermissionRule("write", "/.env.*", "deny"),
    PermissionRule("write", "/.git/**", "deny"),
)


def build_deepagents_permissions(
    rules: tuple[PermissionRule, ...],
    mode: str = "build",
) -> list[FilesystemPermission]:
    """将 PermissionRule 转换为 Deep Agents 接受的 FilesystemPermission 列表。

    FilesystemPermission 仅支持 read / write 两种 operations。
    mode="plan" 时仅保留 read 权限（只读分析）。

    Args:
        rules: PermissionRule 规则元组。
        mode: "plan" 只读 | "build" 读写。

    Returns:
        FilesystemPermission 列表。
    """
    fs_rules = [r for r in rules if r.tool in ("read", "write")]
    if mode == "plan":
        fs_rules = [r for r in fs_rules if r.tool == "read"]

    result: list[FilesystemPermission] = []
    for r in fs_rules:
        mode_val = "interrupt" if r.action == "ask" else r.action
        result.append(
            FilesystemPermission(
                operations=[r.tool],
                paths=[r.pattern],
                mode=mode_val,
            )
        )
    return result
