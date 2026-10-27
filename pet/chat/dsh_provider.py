# -*- coding: utf-8 -*-
"""DSH Web API Provider：通过 dsh-web-service 会话 API 实现连续对话。

自用版新增模块（挂载式）：
- DshWebApiProvider：用 dsh-web-service 的 /sessions/:id/prompt-stream 实现 SSE 流式对话。
  每个素材 ID（character_id）对应一个独立的 DSH 会话，切换角色自动切换会话。
  会话 title 随角色显示名（DisplayName）动态更新（PUT /sessions/:id）。
  支持图片附件上传。
- ProviderRouter：按 config.provider_id 路由到 DSH 或原 OpenAI provider。
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import sys
import threading
from pathlib import Path
from typing import Any, Iterator

from .providers import OpenAICompatibleProvider, ProviderError, StreamEvent
from ..dsh_api import DshApiClient, default_workspace_path
from ..dsh_workspace import get_workspace_title


_DSH_PROVIDER_ID = "dsh-webapi"
_DEFAULT_BASE = "http://127.0.0.1:3080/api/v1"
_APP_DIR_NAME = "dsh-pet-chubby_blue_whale"


def _session_file() -> Path:
    """会话持久化文件路径（数据目录下 dsh_session.json）。"""
    if os.name == 'nt':
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
        return Path(base) / _APP_DIR_NAME / 'dsh_session.json'
    elif sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Application Support' / _APP_DIR_NAME / 'dsh_session.json'
    else:
        return Path.home() / '.config' / _APP_DIR_NAME / 'dsh_session.json'


def _load_persisted() -> dict:
    """读取持久化数据。文件不存在或损坏返回空 dict。

    格式：{"workspace_id": "...", "sessions": {char_id: {session_id, system_sent, last_title}}}
    兼容旧格式（单会话 {"session_id": "...", ...}）自动迁移。
    """
    try:
        f = _session_file()
        if f.exists():
            data = json.loads(f.read_text(encoding='utf-8'))
            if isinstance(data, dict):
                if 'sessions' not in data and data.get('session_id'):
                    char_id = data.get('character_id', '_default')
                    data = {
                        'workspace_id': data.get('workspace_id'),
                        'sessions': {char_id: {
                            'session_id': data['session_id'],
                            'system_sent': data.get('system_sent', False),
                            'last_title': data.get('last_title', ''),
                        }},
                    }
                return data
    except Exception:
        pass
    return {}


def _save_persisted(workspace_id: str | None, sessions: dict) -> None:
    """写入持久化数据。"""
    try:
        f = _session_file()
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({
            'workspace_id': workspace_id,
            'sessions': sessions,
        }, ensure_ascii=False), encoding='utf-8')
    except Exception:
        logging.exception("保存 DSH 会话信息失败")


def _clear_persisted() -> None:
    """删除持久化会话文件。"""
    try:
        f = _session_file()
        if f.exists():
            f.unlink()
    except Exception:
        pass


def _is_session_invalid_error(text: str) -> bool:
    """判断错误是否表示会话不存在（404 或 not found）。"""
    lower = text.lower()
    return "404" in lower or "not found" in lower or "no such session" in lower


def _make_title(char_name: str) -> str:
    """根据角色显示名生成会话 title。"""
    return f"{char_name}对话" if char_name.strip() else "桌宠对话"


class DshWebApiProvider:
    """通过 dsh-web-service 会话 API 实现的对话 Provider。

    每个素材 ID（character_id）对应一个独立的 DSH 会话：
    - 首次对话时创建会话，title 用当前角色显示名。
    - 后续对话复用同一会话，保证 DSH 侧上下文连续。
    - 如果角色显示名变化，自动调用 PUT /sessions/:id 更新 title。
    支持图片附件：解析 messages 中的 image_url → 上传到 DSH 会话 → 提示中引用。
    """

    def __init__(self):
        persisted = _load_persisted()
        self._workspace_id: str | None = persisted.get("workspace_id") or None
        self._sessions: dict[str, dict] = persisted.get("sessions", {})
        if not isinstance(self._sessions, dict):
            self._sessions = {}
        self._client: DshApiClient | None = None
        if self._sessions:
            logging.info("DSH 会话从持久化恢复: %d 个角色", len(self._sessions))

    def _ensure_client(self, config) -> DshApiClient:
        if self._client is None:
            base_url = config.base_url or _DEFAULT_BASE
            self._client = DshApiClient(base_url=base_url, api_key=config.api_key)
        return self._client

    def _ensure_workspace(self, client) -> str | None:
        if self._workspace_id is None:
            ws_path = default_workspace_path()
            ws_title = get_workspace_title()
            try:
                self._workspace_id = client.ensure_workspace(ws_path, ws_title)
            except Exception:
                logging.exception("DSH 工作区创建失败，继续无工作区")
        return self._workspace_id

    def _get_char_id(self, config) -> str:
        return getattr(config, 'character_id', '') or '_default'

    def _ensure_session(self, config) -> tuple[str, str]:
        """按 character_id 获取或创建会话，返回 (session_id, char_id)。"""
        char_id = self._get_char_id(config)
        client = self._ensure_client(config)
        info = self._sessions.get(char_id)
        if info and info.get('session_id'):
            return info['session_id'], char_id
        self._ensure_workspace(client)
        char_name = getattr(config, 'character_name', '') or ''
        session_title = _make_title(char_name)
        try:
            session_id = client.create_session(
                workspace_id=self._workspace_id,
                title=session_title,
                model=config.model or None,
            )
        except Exception as exc:
            raise ProviderError(f"DSH 会话创建失败: {exc}", 503) from exc
        if not session_id:
            raise ProviderError("DSH 会话创建返回空 ID", 503)
        self._sessions[char_id] = {
            'session_id': session_id,
            'system_sent': False,
            'last_title': session_title,
        }
        _save_persisted(self._workspace_id, self._sessions)
        return session_id, char_id

    def _maybe_update_title(self, client, config, char_id: str) -> None:
        """如果角色显示名与上次记录的 title 不同，更新 DSH 会话 title。"""
        info = self._sessions.get(char_id)
        if not info or not info.get('session_id'):
            return
        char_name = getattr(config, 'character_name', '') or ''
        new_title = _make_title(char_name)
        if new_title == info.get('last_title'):
            return
        session_id = info['session_id']
        if client.update_session(session_id, title=new_title):
            info['last_title'] = new_title
            _save_persisted(self._workspace_id, self._sessions)

    def _invalidate_session(self, char_id: str) -> None:
        """该角色的会话失效时重置，下次 _ensure_session 创建新会话。"""
        logging.warning("DSH 会话失效 (char_id=%s)，重置后将创建新会话", char_id)
        self._sessions.pop(char_id, None)
        _save_persisted(self._workspace_id, self._sessions)

    def _extract_user_message(self, messages: list[dict]) -> tuple[str, bytes | None]:
        """从 messages 最后一条 user 消息提取文本和图片。"""
        last = messages[-1] if messages else {}
        text = ""
        image: bytes | None = None
        content = last.get("content", "")
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            for part in content:
                if not isinstance(part, dict):
                    continue
                ptype = part.get("type", "")
                if ptype == "text":
                    text += part.get("text", "")
                elif ptype == "image_url":
                    url = part.get("image_url", {}).get("url", "")
                    if url.startswith("data:") and "," in url:
                        _, b64 = url.split(",", 1)
                        try:
                            image = base64.b64decode(b64)
                        except Exception:
                            logging.exception("解析图片 base64 失败")
        return text, image

    def stream(
        self,
        messages: list[dict[str, Any]],
        config: Any,
        cancel_event: threading.Event,
        response_holder: list | None = None,
    ) -> Iterator[str | StreamEvent]:
        """Provider 接口：流式对话。

        每个素材 ID 对应一个 DSH 会话，切换角色自动切换会话。
        yield str 为正文增量，yield StreamEvent('reasoning', text) 为思考过程。
        会话失效（404）时自动重置并重试一次。
        """
        client = self._ensure_client(config)
        user_text, image_bytes = self._extract_user_message(messages)
        if not user_text and image_bytes is None:
            return

        for attempt in range(2):
            session_id, char_id = self._ensure_session(config)
            info = self._sessions[char_id]

            if not info.get('system_sent'):
                sys_msg = next((m for m in messages if m.get("role") == "system"), None)
                if sys_msg:
                    sys_text = sys_msg.get("content", "")
                    if isinstance(sys_text, str) and sys_text.strip():
                        try:
                            client.prompt_sync(session_id, sys_text)
                        except Exception:
                            logging.exception("发送 system prompt 到 DSH 失败")
                info['system_sent'] = True
                _save_persisted(self._workspace_id, self._sessions)

            self._maybe_update_title(client, config, char_id)

            prompt_text = user_text
            if image_bytes:
                try:
                    file_path = client.upload_file(session_id, image_bytes, "screenshot.jpg")
                    if file_path:
                        prompt_text = user_text + f"\n[请查看附件: {file_path}]"
                except Exception:
                    logging.exception("上传截图到 DSH 失败")

            session_invalid = False
            for kind, text in client.prompt_stream(session_id, prompt_text, cancel_event):
                if cancel_event is not None and cancel_event.is_set():
                    break
                if kind == "delta":
                    yield text
                elif kind == "reasoning":
                    yield StreamEvent(kind="reasoning", text=text)
                elif kind == "error":
                    if attempt == 0 and _is_session_invalid_error(text):
                        session_invalid = True
                        break
                    raise ProviderError(text, 503)

            if session_invalid:
                self._invalidate_session(char_id)
                continue
            return

    def reset_session(self) -> None:
        """重置所有会话（下次 stream 创建新 DSH 会话）。"""
        self._sessions.clear()
        _clear_persisted()


class ProviderRouter:
    """按 config.provider_id 路由到 DSH 或原 OpenAI provider。

    注入到 ChatService 替代默认的 OpenAICompatibleProvider，
    当 provider_id == 'dsh-webapi' 时走 DSH 会话 API，否则走原 OpenAI 兼容接口。
    """

    def __init__(self):
        self._openai: OpenAICompatibleProvider | None = None
        self._dsh: DshWebApiProvider | None = None

    def stream(
        self,
        messages: list[dict[str, Any]],
        config: Any,
        cancel_event: threading.Event,
        response_holder: list | None = None,
    ) -> Iterator[str | StreamEvent]:
        if getattr(config, "provider_id", "") == _DSH_PROVIDER_ID:
            if self._dsh is None:
                self._dsh = DshWebApiProvider()
            yield from self._dsh.stream(messages, config, cancel_event, response_holder)
            return
        if self._openai is None:
            self._openai = OpenAICompatibleProvider()
        yield from self._openai.stream(messages, config, cancel_event, response_holder)