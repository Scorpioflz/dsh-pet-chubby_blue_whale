# -*- coding: utf-8 -*-
"""DSH 工作区管理：角色绑定工作区，切换角色时检查绑定，无则弹窗要求提供工作区名称。

文件位置：数据目录下 dsh_workspaces.json，内容：
{
  "default_title": "pet",  # 全局默认工作区标题（非角色相关功能用）
  "characters": {
    "char_id_1": {"title": "蓝鲸"},
    "char_id_2": {"title": "猫咪"}
  }
}
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _config_file() -> Path:
    """工作区配置文件路径（数据目录下）。"""
    if os.name == 'nt':
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
        return Path(base) / 'dsh-pet-chubby_blue_whale' / 'dsh_workspaces.json'
    elif sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Application Support' / 'dsh-pet-chubby_blue_whale' / 'dsh_workspaces.json'
    else:
        return Path.home() / '.config' / 'dsh-pet-chubby_blue_whale' / 'dsh_workspaces.json'


def _legacy_file() -> Path:
    """旧版工作区配置文件路径（dsh_workspace.json）。"""
    return _config_file().parent / 'dsh_workspace.json'


def _load() -> dict:
    """读取工作区配置（线程安全，不弹窗）。"""
    try:
        f = _config_file()
        if f.exists():
            data = json.loads(f.read_text(encoding='utf-8'))
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    # 迁移旧版单工作区配置
    try:
        lf = _legacy_file()
        if lf.exists():
            legacy = json.loads(lf.read_text(encoding='utf-8'))
            if isinstance(legacy, dict) and legacy.get('title'):
                return {"default_title": str(legacy['title']).strip(), "characters": {}}
    except Exception:
        pass
    return {"default_title": "pet", "characters": {}}


def _save(data: dict) -> None:
    try:
        f = _config_file()
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    except Exception:
        pass


def get_workspace_title() -> str:
    """全局默认工作区标题（非角色相关功能用）。"""
    return str(_load().get('default_title', 'pet')).strip() or 'pet'


def ensure_workspace_title(parent=None) -> str:
    """确保全局默认工作区标题已配置：首次弹窗询问，后续读取。"""
    data = _load()
    if data.get('default_title'):
        return data['default_title']
    title = 'pet'
    try:
        from PySide6.QtWidgets import QInputDialog
        title, ok = QInputDialog.getText(
            parent, 'DSH 工作区', '首次启动，请输入默认 DSH 工作区名称：', text='pet'
        )
        if not ok or not title.strip():
            title = 'pet'
        title = title.strip()
    except Exception:
        title = 'pet'
    data['default_title'] = title
    _save(data)
    return title


def get_character_workspace_title(char_id: str) -> str | None:
    """获取$色绑定的工作区标题，未绑定返回 None。"""
    data = _load()
    chars = data.get('characters', {})
    info = chars.get(char_id)
    if isinstance(info, dict) and info.get('title'):
        return str(info['title']).strip()
    return None


def ensure_character_workspace_title(char_id: str, char_name: str = '', parent=None) -> str:
    """确保角色已绑定工作区标题：已绑定直接返回，未绑定弹窗要求输入。

    char_name 用于弹窗提示和默认值建议。
    """
    data = _load()
    chars = data.get('characters', {})
    info = chars.get(char_id)
    if isinstance(info, dict) and info.get('title'):
        return str(info['title']).strip()

    default_title = char_name.strip() or char_id
    title = default_title
    try:
        from PySide6.QtWidgets import QInputDialog
        title, ok = QInputDialog.getText(
            parent, '绑定工作区',
            f'角色「{char_name or char_id}」尚未绑定 DSH 工作区。\n请输入工作区名称：',
            text=default_title
        )
        if not ok or not title.strip():
            title = default_title
        title = title.strip()
    except Exception:
        title = default_title

    chars[char_id] = {"title": title}
    data['characters'] = chars
    _save(data)
    return title


def bind_character_workspace(char_id: str, title: str) -> None:
    """直接绑定角色工作区标题（不弹窗，用于程序化设置）。"""
    data = _load()
    chars = data.get('characters', {})
    chars[char_id] = {"title": str(title).strip()}
    data['characters'] = chars
    _save(data)


def unbind_character_workspace(char_id: str) -> None:
    """解除角色工作区绑定。"""
    data = _load()
    chars = data.get('characters', {})
    chars.pop(char_id, None)
    data['characters'] = chars
    _save(data)

def get_character_memory_enabled(char_id: str) -> bool:
    """角色记忆开关：默认开启（当前激活的角色记录记忆）。"""
    data = _load()
    chars = data.get('characters', {})
    info = chars.get(char_id)
    if isinstance(info, dict):
        return info.get('memory_enabled', True)
    return True


def set_character_memory_enabled(char_id: str, enabled: bool) -> None:
    """设置角色记忆开关。"""
    data = _load()
    chars = data.get('characters', {})
    info = chars.get(char_id)
    if not isinstance(info, dict):
        info = {}
        chars[char_id] = info
    info['memory_enabled'] = bool(enabled)
    data['characters'] = chars
    _save(data)