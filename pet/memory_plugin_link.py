# -*- coding: utf-8 -*-
"""DSH 记忆插件（@dsh-pet/memory）安装状态检查。

桌宠的记忆功能已下沉到 DSH 插件层（integrations/dsh-pet-memory），按工作区
共享记忆。本模块在启动时检查插件是否已安装到 DSH profile，未安装时提醒用户
去设置页安装——与 dsh-pet-bridge 不同，这里**不自动安装**，只检查 + 提醒，
因为记忆插件是可选增强，不是联动的硬依赖。

检查逻辑与 agent_link 的桥接插件检查同源（读 profile 的 package.json
dependencies），但独立实现以避免依赖 agent_link 的私有函数。
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

log = logging.getLogger(__name__)

MEMORY_PLUGIN_NAME = "@dsh-pet/memory"

DSH_PROFILE_HOME = Path(os.environ.get("DSH_HOME", str(Path.home() / ".dsh")))


def bundled_plugin_dir() -> Path | None:
    """内置记忆插件目录：打包版在 sys._MEIPASS，源码运行在仓库 integrations/ 下。

    与 ``agent_link.DshMonitor.bundled_plugin_dir`` 同一约定。
    """
    candidates: list[Path] = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "integrations" / "dsh-pet-memory")
    candidates.append(
        Path(__file__).resolve().parent.parent / "integrations" / "dsh-pet-memory"
    )
    for c in candidates:
        if (c / "package.json").is_file():
            return c
    return None


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
    """返回 (内置插件目录存在, 已安装到至少一个 profile)。

    内置目录缺失 = 打包/源码环境异常；已安装 = 用户无需操作。
    两者都满足才算"就绪"——内置在但没装，需要提醒用户安装。
    """
    return bundled_plugin_dir() is not None, is_installed()

def _manifest_set_memory_bundle(pkg: dict, profile_dir: Path, present: bool) -> bool:
    """保持 dsh.profile.bundles 与记忆插件安装状态一致，返回是否发生写入。"""
    bundles = (
        pkg.setdefault("dsh", {}).setdefault("profile", {})
        .setdefault("bundles", [])
    )
    has = MEMORY_PLUGIN_NAME in bundles
    if present and not has:
        bundles.append(MEMORY_PLUGIN_NAME)
    elif not present and has:
        bundles.remove(MEMORY_PLUGIN_NAME)
    else:
        return False
    (profile_dir / "package.json").write_text(
        json.dumps(pkg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return True


def install_memory_plugin() -> tuple[bool, str]:
    """一键安装记忆插件到所有真实存在的 dsh profile。

    与 ``agent_link.DshMonitor.install_bridge`` 同源逻辑（pnpm add + bundles 维护），
    复用 agent_link 的 pnpm 工具函数以保持安装行为一致。返回 (成功与否, 说明)。
    """
    from .agent_link import (
        _ensure_profile,
        _pnpm_command,
        _read_manifest,
        _run_pnpm_repairing_specs,
        _which,
    )

    plugin = bundled_plugin_dir()
    if plugin is None:
        return False, "找不到内置记忆插件（integrations/dsh-pet-memory）"
    if _which("node") is None and _pnpm_command() is None:
        return False, "找不到 node，请先安装 Node.js（需包含 npm）"
    if _pnpm_command() is None:
        return False, "找不到 pnpm，可运行 npm install -g pnpm 安装"

    profiles = _real_profiles()
    if not profiles:
        if not _ensure_profile(DSH_PROFILE_HOME / "profiles" / "web"):
            return False, ("没有可用的 dsh profile，且自动补齐默认 web profile 失败")
        profiles = _real_profiles()
        if not profiles:
            return False, "补齐默认 web profile 后仍未识别到 dsh profile"

    failed: list[str] = []
    succeeded: list[str] = []
    for profile in profiles:
        pkg = _read_manifest(profile)
        if pkg is None:
            failed.append(f"{profile.name}: package.json 读取失败")
            continue
        if _profile_has_plugin(profile):
            rc, out, _repaired = _run_pnpm_repairing_specs(profile, "add", str(plugin))
            if rc != 0:
                failed.append(f"{profile.name}: pnpm refresh 失败 {(out or '')[-150:]}")
                continue
            pkg = _read_manifest(profile)
            if pkg is None:
                failed.append(f"{profile.name}: 刷新后 package.json 读取失败")
                continue
            try:
                _manifest_set_memory_bundle(pkg, profile, True)
            except Exception as exc:
                failed.append(f"{profile.name}: bundles 写入失败 {exc}")
                continue
            succeeded.append(profile.name)
            continue
        rc, out, _repaired = _run_pnpm_repairing_specs(profile, "add", str(plugin))
        if rc != 0:
            failed.append(f"{profile.name}: pnpm add 失败 {(out or '')[-150:]}")
            continue
        pkg = _read_manifest(profile)
        if pkg is None:
            failed.append(f"{profile.name}: 安装后 package.json 读取失败")
            continue
        try:
            _manifest_set_memory_bundle(pkg, profile, True)
        except Exception as exc:
            failed.append(f"{profile.name}: bundles 写入失败 {exc}")
            continue
        succeeded.append(profile.name)
    if failed:
        return False, "部分实例安装失败——" + "；".join(failed)
    return True, f"记忆插件已安装到 {len(succeeded)} 个 dsh 实例（{', '.join(succeeded)}）"