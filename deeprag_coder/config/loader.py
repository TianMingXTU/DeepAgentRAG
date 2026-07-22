"""分层配置加载器 — 4 层合并（Defaults → Global JSON → Project JSON → Env）。

优先级（低 → 高）:
  1. Defaults: Settings() dataclass 默认值
  2. Global: ~/.config/deeprag/deeprag.json
  3. Project: ./deeprag.json
  4. Env: 环境变量（最高优先级，兼容 .env）
"""

import json
import os
from dataclasses import fields, is_dataclass, replace
from pathlib import Path

from deeprag_coder.config.settings import Settings


CONFIG_PATHS = [
    Path("~/.config/deeprag/deeprag.json").expanduser(),
    Path.cwd() / "deeprag.json",
]


def load_config() -> Settings:
    """加载配置：Defaults → Global → Project → Env 逐层合并。

    Returns:
        合并后的 Settings 实例。
    """
    cfg = Settings()
    for p in CONFIG_PATHS:
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                cfg = _merge_dataclass(cfg, data)
            except (json.JSONDecodeError, OSError):
                pass
    # Env 覆盖在 Settings.__post_init__ 中处理
    return cfg


def _merge_dataclass(obj: Settings, data: dict) -> Settings:
    """浅合并 dataclass 字段，嵌套 dataclass 递归合并。"""
    updates = {}
    for f in fields(obj):
        if f.name in data:
            val = data[f.name]
            if is_dataclass(f.type) and isinstance(val, dict):
                updates[f.name] = _merge_dataclass(getattr(obj, f.name), val)
            else:
                updates[f.name] = val
    return replace(obj, **updates)
