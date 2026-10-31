# -*- coding: utf-8 -*-
"""DSH Web API 插件（dsh-web-service）安装状态检查。

桌宠的对话、截图问答、自言自语等全部通过 dsh-web-service 插件暴露的
HTTP API（http://127.0.0.1:3080/api/v1）与 DSH 通信。没有此插件，
桌宠无法对话——这是硬依赖，不是可选增强。

本模块检查插件是否已安装到 DSH profile，未安装时提醒用户安装。
与 memory_plugin_link 不同，这里不自动安装（插件不在桌宠 integrations/ 中，
需从 GitHub 安装），只检查 + 给出安装命令。

检查逻辑与 memory_plugin_link 同源（读 profile 的 package.json dependencies）。
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

WEBAPI_PLUGIN_NAME = "dsh-web-service"
WEBAPI_INSTALL_URL = "https://github.com/toddpan/dsh-webapi#readme"
WEBAPI_INSTALL_CMD = "dsh plugin --profile web add github:toddpan/dsh-webapi"

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
    """检查单个 profile 的 package.json 是否声明了 webapi 插件依赖。"""
    try:
        pkg = json.loads(
            (profile_dir / "package.json").read_text(encoding="utf-8")
        )
    except Exception:
        return False
    return WEBAPI_PLUGIN_NAME in ((pkg.get("dependencies") or {}) or {})


def is_installed() -> bool:
    """webapi 插件是否已安装到至少一个 DSH profile。"""
    return any(_profile_has_plugin(p) for p in _real_profiles())


def installed_profiles() -> list[str]:
    """已安装 webapi 插件的 profile 名称列表（用于状态展示）。"""
    return [p.name for p in _real_profiles() if _profile_has_plugin(p)]