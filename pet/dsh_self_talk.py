# -*- coding: utf-8 -*-
"""DSH 自动生成自言自语候选词。

每天通过 DSH API 以桌宠身份生成自言自语候选词。
包含身份设定（System Prompt），内容自然生动，仿佛桌宠在播报消息、吐槽。
候选词和时间戳存到独立文件 dsh_self_talk_texts.json，不写 config.json。
"""

from __future__ import annotations

import json as _json
import logging
import time
from pathlib import Path
from typing import Any


_GENERATE_PROMPT = """请以桌宠的口吻生成 60 条自言自语，可以包含今日热搜、新闻感想、日常碎碎念、每日要闻等等，每条一句话。内容要自然、生动、有趣，仿佛真的是个桌宠在播报消息、吐槽。每条一行，不要编号，不要多余解释。"""

_INTERVAL_SECONDS = 86400  # 24 hours


def _texts_file(config: Any) -> Path:
    """独立文件路径：dsh_self_talk_texts.json（存候选词 + 时间戳）。"""
    return config.dir / "dsh_self_talk_texts.json"


def _load_texts_data(config: Any) -> dict:
    """读取独立文件，返回 {"texts": [...], "last_generated": float}。"""
    f = _texts_file(config)
    if not f.is_file():
        return {"texts": [], "last_generated": 0.0}
    try:
        data = _json.loads(f.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return {"texts": data, "last_generated": 0.0}
        return data
    except Exception:
        return {"texts": [], "last_generated": 0.0}


def _save_texts_data(config: Any, texts: list[str], ts: float) -> None:
    """写入独立文件。"""
    f = _texts_file(config)
    f.write_text(
        _json.dumps({"texts": texts, "last_generated": ts}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _build_prompt(system_prompt: str) -> str:
    """构建生成提示（含身份设定）。"""
    if system_prompt and system_prompt.strip():
        return f"{system_prompt.strip()}\n\n{_GENERATE_PROMPT}"
    return _GENERATE_PROMPT


def _parse_lines(reply: str) -> list[str]:
    """解析回复，提取候选词列表。"""
    if not reply:
        return []
    lines = []
    for raw in reply.strip().splitlines():
        text = raw.strip()
        if not text:
            continue
        for prefix_len in range(1, 5):
            if len(text) > prefix_len + 1 and text[:prefix_len].isdigit():
                sep = text[prefix_len]
                if sep in '.、）)．:：':
                    text = text[prefix_len + 1:].strip()
                    break
        if len(text) >= 2 and text[0] in '"「『（(' and text[-1] in '"」』）)':
            text = text[1:-1].strip()
        if text and len(text) <= 200:
            lines.append(text)
    return lines


def generate_self_talk(config: Any) -> bool:
    """通过 DSH API 生成自言自语候选词，写入独立文件。

    Returns: True 如果成功生成并保存，False 如果跳过或失败。
    """
    try:
        if not config.get("dsh_self_talk_enabled", False):
            return False

        data = _load_texts_data(config)
        last = float(data.get("last_generated", 0) or 0)
        if last and (time.time() - last) < _INTERVAL_SECONDS:
            return False

        settings = config.chat_settings()
        system_prompt = str(settings.default_system_prompt or "")
        provider = settings.active_config
        if getattr(provider, "provider_id", "") != "dsh-webapi":
            return False

        from .dsh_api import DshApiClient, default_workspace_path
        from .dsh_workspace import get_workspace_title

        client = DshApiClient(base_url=provider.base_url, api_key=provider.api_key)
        if not client.is_available():
            logging.warning("DSH 不可用，跳过自言自语生成")
            return False

        ws_id = client.ensure_workspace(default_workspace_path(), get_workspace_title())
        sessions = client.list_sessions(workspace_id=ws_id)
        if sessions:
            session_id = sessions[-1].get("id") or sessions[-1].get("sessionId")
        else:
            session_id = client.create_session(workspace_id=ws_id, title="自言自语生成")
        if not session_id:
            return False

        prompt = _build_prompt(system_prompt)
        reply = client.prompt_sync(session_id, prompt)
        if not reply:
            return False

        new_texts = _parse_lines(reply)
        if not new_texts:
            return False

        _save_texts_data(config, new_texts, time.time())
        logging.info("DSH 自言自语生成成功: %d 条 (写入 dsh_self_talk_texts.json)", len(new_texts))
        return True

    except Exception:
        logging.exception("DSH 自言自语生成失败")
        return False