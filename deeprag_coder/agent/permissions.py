"""文件系统权限规则 — 保护源码不被 AI 误写。"""

from deepagents import FilesystemPermission

# 拒绝写入 deeprag_coder/ 自身源码
DENY_SELF_WRITE = FilesystemPermission(
    operations=["write"],
    paths=["/deeprag_coder/**"],
    mode="deny",
)

# 拒绝写入 .env 等敏感文件
DENY_ENV_WRITE = FilesystemPermission(
    operations=["write"],
    paths=["/.env", "/.env.*"],
    mode="deny",
)

# 拒绝写入 .git 目录
DENY_GIT_WRITE = FilesystemPermission(
    operations=["write"],
    paths=["/.git/**"],
    mode="deny",
)

# 默认权限规则集
DEFAULT_PERMISSIONS = [
    DENY_SELF_WRITE,
    DENY_ENV_WRITE,
    DENY_GIT_WRITE,
]
