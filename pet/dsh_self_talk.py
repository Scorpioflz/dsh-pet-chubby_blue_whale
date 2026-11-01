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


_GENERATE_PROMPT = """请以桌宠的口吻生成 60-100 条自言自语，可以包含今日热搜、新闻感想、日常碎碎念、每日要闻等等，每条一句话。内容要自然、生动、有趣，仿佛真的是个桌宠在播报消息、吐槽。每条一行，不要编号，不要多余解释。"""

_LEGACY_INTERVAL_SECONDS = 86400  # 24h（schedule 为空时的旧行为）
_DEFAULT_SCHEDULE = "08:00"
_MAX_CHECK_DELAY_MS = 10 * 60 * 1000  # 10 分钟（旧行为定期检查间隔上限）


def _parse_hhmm(schedule: str) -> tuple[int, int] | None:
    """解析 ``HH:MM`` → ``(hour, minute)``；无效返回 None。"""
    if not schedule or not isinstance(schedule, str):
        return None
    parts = schedule.strip().split(":")
    if len(parts) != 2:
        return None
    try:
        hour, minute = int(parts[0]), int(parts[1])
    except ValueError:
        return None
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return (hour, minute)


def _clean_weekdays(value: Any) -> list[int]:
    """清洗星期筛选列表：空 = 每天；否则 [1..7]（1=周一…7=周日）。"""
    if not isinstance(value, (list, tuple)):
        return []
    return [int(w) for w in value if isinstance(w, (int, float)) and 1 <= int(w) <= 7]


def _next_schedule_after(after_ts: float, hour: int, minute: int, weekdays: list[int]) -> float:
    """找 ``after_ts`` 之后第一个匹配星期的计划点（HH:MM），返回 Unix 时间戳。

    ``weekdays`` 空列表 = 每天；否则 [1..7]（1=周一…7=周日）。
    """
    after_tm = time.localtime(after_ts)
    day_iter = time.mktime((after_tm.tm_year, after_tm.tm_mon, after_tm.tm_mday,
                            hour, minute, 0, 0, 0, -1))
    if day_iter <= after_ts:
        day_iter += 86400
    for _ in range(8):
        wd = time.localtime(day_iter).tm_wday + 1
        if not weekdays or wd in weekdays:
            return day_iter
        day_iter += 86400
    return day_iter


def _should_run_now(config: Any, data: dict) -> bool:
    """按定时计划判断是否应该运行。

    - ``dsh_self_talk_schedule`` 为空或无效 → 旧行为（24h 滑动窗口）
    - 非空 → 定时计划模式：检查 ``(last_run, now]`` 之间是否有计划点
    """
    schedule = str(config.get("dsh_self_talk_schedule", "") or "")
    last_run = float(data.get("last_generated", 0) or 0)
    now = time.time()

    parsed = _parse_hhmm(schedule)
    if parsed is None:
        return (now - last_run) >= _LEGACY_INTERVAL_SECONDS

    hour, minute = parsed
    weekdays = _clean_weekdays(config.get("dsh_self_talk_weekdays"))

    if last_run <= 0:
        now_tm = time.localtime(now)
        today_target = time.mktime((now_tm.tm_year, now_tm.tm_mon, now_tm.tm_mday,
                                    hour, minute, 0, 0, 0, -1))
        if now >= today_target:
            if not weekdays or (now_tm.tm_wday + 1) in weekdays:
                return True
        return False

    next_target = _next_schedule_after(last_run, hour, minute, weekdays)
    return now >= next_target


def next_check_delay_ms(config: Any) -> int:
    """计算到下一次检查碎碎念生成的延迟（毫秒）。

    - 定时计划模式：精确到下一个计划点
    - 旧行为模式：固定 10 分钟
    """
    schedule = str(config.get("dsh_self_talk_schedule", "") or "")
    parsed = _parse_hhmm(schedule)
    if parsed is None:
        return _MAX_CHECK_DELAY_MS
    hour, minute = parsed
    weekdays = _clean_weekdays(config.get("dsh_self_talk_weekdays"))
    now = time.time()
    next_target = _next_schedule_after(now, hour, minute, weekdays)
    delay_ms = int(max(1000, (next_target - now) * 1000))
    return min(delay_ms, _MAX_CHECK_DELAY_MS)


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
        if not _should_run_now(config, data):
            return False

        settings = config.chat_settings()
        system_prompt = str(settings.default_system_prompt or "")
        provider = settings.active_config
        if getattr(provider, "provider_id", "") != "dsh-webapi":
            return False

        from .dsh_api import DshApiClient, default_workspace_path
        from .dsh_workspace import get_workspace_title

        # 复用 provider 的 API Key（可能存在 keyring 中，需要 resolve）
        api_key = provider.api_key
        if not api_key:
            try:
                api_key = config.resolve_api_key(provider)
            except Exception:
                pass

        client = DshApiClient(base_url=provider.base_url, api_key=api_key)
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