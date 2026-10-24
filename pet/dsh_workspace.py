# -*- coding: utf-8 -*-
"""DSH 工作区标题管理：首次启动弹窗询问，后续读取文件。

文件位置：数据目录下 dsh_workspace.json，内容 {"title": "pet"}。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _workspace_file() -> Path:
    """工作区配置文件路径（数据目录下）。"""
    if os.name == 'nt':
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
        return Path(base) / 'dsh-pet-standalone' / 'dsh_workspace.json'
    elif sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Application Support' / 'dsh-pet-standalone' / 'dsh_workspace.json'
    else:
        return Path.home() / '.config' / 'dsh-pet-standalone' / 'dsh_workspace.json'


def get_workspace_title() -> str:
    """读取工作区标题（线程安全，不弹窗）。文件不存在返回默认值 'pet'。"""
    try:
        f = _workspace_file()
        if f.exists():
            return str(json.loads(f.read_text(encoding='utf-8')).get('title', 'pet')).strip() or 'pet'
    except Exception:
        pass
    return 'pet'


def ensure_workspace_title(parent=None) -> str:
    """确保工作区标题已配置：首次弹窗询问，后续读取（GUI 线程调用）。"""
    f = _workspace_file()
    if f.exists():
        return get_workspace_title()
    title = 'pet'
    try:
        from PySide6.QtWidgets import QInputDialog
        title, ok = QInputDialog.getText(
            parent, 'DSH 工作区', '首次启动，请输入 DSH 工作区名称：', text='pet'
        )
        if not ok or not title.strip():
            title = 'pet'
        title = title.strip()
    except Exception:
        title = 'pet'
    try:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({'title': title}, ensure_ascii=False), encoding='utf-8')
    except Exception:
        pass
    return title