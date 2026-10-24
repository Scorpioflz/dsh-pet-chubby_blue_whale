# -*- coding: utf-8 -*-
"""DSH Web Service API 客户端：通过 dsh-web-service 插件接入 DSH。

封装工作区管理、会话管理、文件上传与 SSE 流式对话，
供 DshWebApiProvider 和"看看屏幕"等功能调用。

API 文档：https://github.com/toddpan/dsh-webapi
SKILL：https://github.com/toddpan/dsh-webapi/blob/main/skills/dsh-web-service/SKILL.md
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Iterator


_DEFAULT_BASE = "http://127.0.0.1:3080/api/v1"
_TIMEOUT = 30
_STREAM_TIMEOUT = 120


class DshApiError(RuntimeError):
    def __init__(self, message: str, status: int = 0):
        super().__init__(message)
        self.status = status


class DshApiClient:
    """DSH Web Service REST API 客户端。"""

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = (base_url or _DEFAULT_BASE).rstrip("/")
        self.api_key = api_key or ""

    @classmethod
    def from_config(cls, config) -> "DshApiClient":
        base_url = str(config.get("dsh_api_url", _DEFAULT_BASE))
        api_key = str(config.get("dsh_api_key", ""))
        return cls(base_url=base_url, api_key=api_key)

    def _headers(self, content_type: str = "application/json") -> dict[str, str]:
        h = {"Content-Type": content_type}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _request(self, method: str, path: str, body: Any = None, timeout: int = _TIMEOUT) -> Any:
        url = f"{self.base_url}{path}"
        data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
                result = json.loads(raw)
                if isinstance(result, dict) and result.get("ok") is False:
                    raise DshApiError(result.get("error", "未知错误"), 500)
                return result
        except urllib.error.HTTPError as exc:
            try:
                err_body = json.loads(exc.read().decode("utf-8"))
                msg = err_body.get("error", err_body.get("message", str(exc)))
            except Exception:
                msg = str(exc)
            raise DshApiError(msg, exc.code) from exc

    def system_status(self) -> dict:
        return self._request("GET", "/system/status")

    def is_available(self) -> bool:
        try:
            self.system_status()
            return True
        except Exception:
            return False

    def list_workspaces(self) -> list[dict]:
        result = self._request("GET", "/workspaces")
        return self._extract_items(result)

    def ensure_workspace(self, path: str, title: str = "pet") -> str | None:
        """确保工作区存在（按 title 匹配），返回 workspaceId。"""
        workspaces = self.list_workspaces()
        for ws in workspaces:
            if ws.get("title") == title or ws.get("path") == path:
                return ws.get("id") or ws.get("workspaceId")
        os.makedirs(path, exist_ok=True)
        result = self._request("POST", "/workspaces", body={"path": path, "title": title})
        ws = self._extract_data(result)
        return ws.get("id") or ws.get("workspaceId") if ws else None

    def list_sessions(self, workspace_id: str | None = None) -> list[dict]:
        path = "/sessions"
        if workspace_id:
            path += "?" + urllib.parse.urlencode({"workspaceId": workspace_id})
        return self._extract_items(self._request("GET", path))

    def create_session(
        self,
        workspace_id: str | None = None,
        title: str | None = None,
        model: str | None = None,
    ) -> str | None:
        body: dict[str, Any] = {}
        if workspace_id:
            body["workspaceId"] = workspace_id
        if title:
            body["title"] = title
        if model:
            body["model"] = model
        result = self._request("POST", "/sessions", body=body)
        data = self._extract_data(result)
        return data.get("id") or data.get("sessionId") if data else None

    def upload_file(self, session_id: str, file_bytes: bytes, filename: str) -> str | None:
        """上传文件到会话工作区，返回文件 path（供提示中引用）。"""
        url = f"{self.base_url}/sessions/{session_id}/files"
        boundary = "----dsh-pet-boundary"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="files"; filename="{filename}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n"
        ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(url, data=body, method="POST", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                data = self._extract_data(result)
                if data and isinstance(data.get("files"), list) and data["files"]:
                    return data["files"][0].get("path")
                return None
        except urllib.error.HTTPError as exc:
            raise DshApiError(f"上传文件失败: {exc}", exc.code) from exc

    def prompt_stream(
        self, session_id: str, prompt: str, cancel_event=None
    ) -> Iterator[tuple[str, str]]:
        """SSE 流式发送提示，yield (kind, text) 元组。

        kind: 'delta'（正文增量）、'reasoning'（思考增量）、'error'。
        """
        url = f"{self.base_url}/sessions/{session_id}/prompt-stream"
        data = json.dumps({"prompt": prompt}, ensure_ascii=False).encode("utf-8")
        headers = self._headers()
        headers["Accept"] = "text/event-stream"
        req = urllib.request.Request(url, data=data, method="POST", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=_STREAM_TIMEOUT) as resp:
                event_type = ""
                for raw_line in resp:
                    if cancel_event is not None and cancel_event.is_set():
                        break
                    line = raw_line.decode("utf-8").rstrip("\r\n")
                    if line.startswith("event:"):
                        event_type = line[6:].strip()
                    elif line.startswith("data:"):
                        payload = line[5:].strip()
                        if not payload or payload == "[DONE]":
                            continue
                        try:
                            event = json.loads(payload)
                        except json.JSONDecodeError:
                            continue
                        if event_type == "delta":
                            delta = event.get("delta", "")
                            if delta:
                                yield ("delta", delta)
                        elif event_type == "reasoning":
                            delta = event.get("delta", "")
                            if delta:
                                yield ("reasoning", delta)
                        elif event_type == "error":
                            yield ("error", event.get("message", "未知错误"))
                    elif line == "":
                        event_type = ""
        except urllib.error.HTTPError as exc:
            yield ("error", f"HTTP {exc.code}: {exc.reason}")
        except Exception as exc:
            yield ("error", str(exc))

    def prompt_sync(self, session_id: str, prompt: str) -> str:
        """同步发送提示并等待回复。"""
        result = self._request(
            "POST", f"/sessions/{session_id}/prompt", body={"prompt": prompt}, timeout=_STREAM_TIMEOUT
        )
        data = self._extract_data(result)
        if data:
            return data.get("content", "")
        return ""

    @staticmethod
    def _extract_data(result: Any) -> Any:
        if isinstance(result, dict):
            return result.get("data", result)
        return result

    @staticmethod
    def _extract_items(result: Any) -> list[dict]:
        data = DshApiClient._extract_data(result)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("items", data.get("sessions", data.get("workspaces", [])))
        return []


def default_workspace_path() -> str:
    """默认工作区目录路径。"""
    return os.path.join(os.path.expanduser("~"), ".dsh-pet-workspace")