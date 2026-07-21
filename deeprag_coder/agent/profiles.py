"""Harness Profiles — 按模型调优 Agent 行为。"""

from deepagents.profiles import (
    HarnessProfile,
    GeneralPurposeSubagentProfile,
)


def coding_profile() -> HarnessProfile:
    """获取针对编码场景调优的 HarnessProfile。

    Returns:
        启用了通用子 Agent 的 HarnessProfile。
    """
    return HarnessProfile(
        general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=True),
    )


# 常用预设
CODING_PROFILE = coding_profile()
