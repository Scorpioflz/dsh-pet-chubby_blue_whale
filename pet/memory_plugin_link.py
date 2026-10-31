# -*- coding: utf-8 -*-
"""DSH 记忆插件（@dsh-cbw/memory）安装状态检查。

记忆插件已提取为独立项目 https://github.com/Scorpioflz/dsh-cbw-memory 。
本模块在启动时检查插件是否已安装到 DSH profile，未安装时提醒用户
去 GitHub 安装——只检查 + 提醒，不自动安装。

检查逻辑与 agent_link 的桥接插件检查同源（读 profile 的 package.json
dependencies），但独立实现以避免依赖 agent_link 的私有函数。
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

MEMORY_PLUGIN_NAME = "@dsh-cbw/memory"

DSH_PROFILE_HOME = Path(os.environ.get("DSH_HOME", str(Path.home() / ".dsh")))


def _real_profiles() -> list[Path]:
    """真实存在的 dsh profile：profiles 目录下含 package.json 的子目录。"""
    profiles_dir = DSH_PROFILE_HOME / "profiles"
    if not profiles_dir.is_dir():
        return []
    return sorted(
        p for p in profiles_dir.iterdir()
        if p.is_dir() and (p / "package.json").is_file()
    )


def _profile_has_plugin(profile_dir: Path) -> bool:
    """检查单个 profile 的 package.json 是否声明了记忆插件依赖。"""
    try:
        pkg = json.loads(
            (profile_dir / "package.json").read_text(encoding="utf-8")
        )
    except Exception:
        return False
    return MEMORY_PLUGIN_NAME in ((pkg.get("dependencies") or {}) or {})


def is_installed() -> bool:
    """记忆插件是否已安装到至少一个 DSH profile。"""
    return any(_profile_has_plugin(p) for p in _real_profiles())


def check_status() -> tuple[bool, bool]:
    """返回 (插件可用, 已安装到至少一个 profile)。

    插件已提取为独立 GitHub 项目，始终可用（第一个返回值恒 True）。
    已安装 = 用户无需操作；未安装 = 需提醒用户去 GitHub 安装。
    """
    return True, is_installed()