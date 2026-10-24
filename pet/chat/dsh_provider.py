# -*- coding: utf-8 -*-
"""DSH Web API Provider：通过 dsh-web-service 会话 API 实现连续对话。

自用版新增模块（挂载式）：
- DshWebApiProvider：用 dsh-web-service 的 /sessions/:id/prompt-stream 实现 SSE 流式对话。
  每个桌宠角色对应一个 DSH 会话（按 system prompt 指纹映射），切换角色自动切换会话。
  支持图片附件上传。
- ProviderRouter：按 config.provider_id 路由到 DSH 或原 OpenAI provider。
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
import threading
from typing import Any, Iterator

from .providers import OpenAICompatibleProvider, ProviderError, StreamEvent
from ..dsh_api import DshApiClient, default_workspace_path


_DSH_PROVIDER_ID = "dsh-webapi"
_DEFAULT_BASE = "http://127.0.0.1:3080/api/v1"


class DshWebApiProvider:
    """通过 dsh-web-service 会话 API 实现的对话 Provider。

    每个桌宠角色（按 system prompt 指纹区分）对应一个 DSH 会话，
    切换角色时自动切换到对应会话，无需修改角色切换代码。
    支持图片附件：解析 messages 中的 image_url → 上传到 DSH 会话 → 提示中引用。
    """

    def __init__(self):
        self._session_map: dict[str, str] = {}
        self._workspace_id: str | None = None
        self._client: DshApiClient | None = None
        self._system_sent: set[str] = set()

    def _ensure_client(self, config) -> DshApiClient:
        if self._client is None:
            base_url = config.base_url or _DEFAULT_BASE
            self._client = DshApiClient(base_url=base_url, api_key=config.api_key)
        return self._client

    @staticmethod
    def _character_key(messages: list[dict]) -> str:
        """从 system prompt 提取角色标识（前 200 字符的 MD5 摘要）。

        不同的角色有不同的 system prompt（人设），指纹自然不同；
        人设部分通常在前 200 字符内，时间等动态内容在后面不影响指纹。
        """
        sys_msg = next((m for m in messages if m.get("role") == "system"), None)
        if sys_msg:
            text = sys_msg.get("content", "")
            if isinstance(text, str) and text.strip():
                return hashlib.md5(text[:200].encode("utf-8")).hexdigest()[:12]
        return "default"

    def _ensure_session(self, config, character_key: str) -> str:
        if character_key in self._session_map:
            return self._session_map[character_key]
        client = self._ensure_client(config)
        if self._workspace_id is None:
            ws_path = default_workspace_path()
            ws_title = getattr(config, "chat_path", "") or "pet"
            try:
                self._workspace_id = client.ensure_workspace(ws_path, ws_title)
            except Exception:
                logging.exception("DSH 工作区创建失败，继续无工作区")
        try:
            session_id = client.create_session(
                workspace_id=self._workspace_id,
                title=f"桌宠-{character_key[:8]}",
                model=config.model or None,
            )
        except Exception as exc:
            raise ProviderError(f"DSH 会话创建失败: {exc}", 503) from exc
        if not session_id:
            raise ProviderError("DSH 会话创建返回空 ID", 503)
        self._session_map[character_key] = session_id
        return session_id

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

        每个角色（system prompt 指纹）对应一个 DSH 会话。
        yield str 为正文增量，yield StreamEvent('reasoning', text) 为思考过程。
        """
        client = self._ensure_client(config)
        char_key = self._character_key(messages)
        session_id = self._ensure_session(config, char_key)

        user_text, image_bytes = self._extract_user_message(messages)
        if not user_text and image_bytes is None:
            return

        if char_key not in self._system_sent:
            sys_msg = next((m for m in messages if m.get("role") == "system"), None)
            if sys_msg:
                sys_text = sys_msg.get("content", "")
                if isinstance(sys_text, str) and sys_text.strip():
                    try:
                        client.prompt_sync(session_id, sys_text)
                    except Exception:
                        logging.exception("发送 system prompt 到 DSH 失败")
            self._system_sent.add(char_key)

        if image_bytes:
            try:
                file_path = client.upload_file(session_id, image_bytes, "screenshot.jpg")
                if file_path:
                    user_text += f"\n[请查看附件: {file_path}]"
            except Exception:
                logging.exception("上传截图到 DSH 失败")

        for kind, text in client.prompt_stream(session_id, user_text, cancel_event):
            if cancel_event is not None and cancel_event.is_set():
                break
            if kind == "delta":
                yield text
            elif kind == "reasoning":
                yield StreamEvent(kind="reasoning", text=text)
            elif kind == "error":
                raise ProviderError(text, 503)

    def reset_session(self, character_key: str | None = None) -> None:
        """重置会话。指定 character_key 时只重置该角色，不指定时重置全部。"""
        if character_key is not None:
            self._session_map.pop(character_key, None)
            self._system_sent.discard(character_key)
        else:
            self._session_map.clear()
            self._system_sent.clear()


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