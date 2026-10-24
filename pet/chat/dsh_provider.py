# -*- coding: utf-8 -*-
"""DSH Web API Provider：通过 dsh-web-service 会话 API 实现连续对话。

自用版新增模块（挂载式）：
- DshWebApiProvider：用 dsh-web-service 的 /sessions/:id/prompt-stream 实现 SSE 流式对话，
  内部维护 DSH session_id 保证连续对话，支持图片附件上传。
- ProviderRouter：按 config.provider_id 路由到 DSH 或原 OpenAI provider。
"""

from __future__ import annotations

import base64
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

    内部维护 DSH session_id：首次调用创建会话，后续复用以保证连续对话。
    支持图片附件：解析 messages 中的 image_url → 上传到 DSH 会话 → 提示中引用。
    """

    def __init__(self):
        self._session_id: str | None = None
        self._workspace_id: str | None = None
        self._client: DshApiClient | None = None
        self._system_sent = False

    def _ensure_client(self, config) -> DshApiClient:
        if self._client is None:
            base_url = config.base_url or _DEFAULT_BASE
            self._client = DshApiClient(base_url=base_url, api_key=config.api_key)
        return self._client

    def _ensure_session(self, config) -> str:
        if self._session_id is not None:
            return self._session_id
        client = self._ensure_client(config)
        if self._workspace_id is None:
            ws_path = default_workspace_path()
            try:
                self._workspace_id = client.ensure_workspace(ws_path, "pet")
            except Exception:
                logging.exception("DSH 工作区创建失败，继续无工作区")
        try:
            self._session_id = client.create_session(
                workspace_id=self._workspace_id,
                title="桌宠对话",
                model=config.model or None,
            )
        except Exception as exc:
            raise ProviderError(f"DSH 会话创建失败: {exc}", 503) from exc
        if not self._session_id:
            raise ProviderError("DSH 会话创建返回空 ID", 503)
        return self._session_id

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

        yield str 为正文增量，yield StreamEvent('reasoning', text) 为思考过程。
        """
        client = self._ensure_client(config)
        session_id = self._ensure_session(config)

        user_text, image_bytes = self._extract_user_message(messages)
        if not user_text and image_bytes is None:
            return

        if not self._system_sent:
            sys_msg = next((m for m in messages if m.get("role") == "system"), None)
            if sys_msg:
                sys_text = sys_msg.get("content", "")
                if isinstance(sys_text, str) and sys_text.strip():
                    try:
                        client.prompt_sync(session_id, sys_text)
                    except Exception:
                        logging.exception("发送 system prompt 到 DSH 失败")
            self._system_sent = True

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

    def reset_session(self) -> None:
        """重置会话（切换桌宠会话时调用，下次 stream 创建新 DSH 会话）。"""
        self._session_id = None
        self._system_sent = False


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