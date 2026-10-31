from __future__ import annotations
import json
from pathlib import Path
from .models import ChatMessage, ChatSettings


def load_character_manifest(root: Path, character_id: str):
    try:
        raw = json.loads((Path(root) / character_id / 'manifest.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    return raw if isinstance(raw, dict) else {}


def load_character_prompt(root: Path, character_id: str):
    chat = load_character_manifest(root, character_id).get('chat', {})
    return str(chat.get('system_prompt', '')) if isinstance(chat, dict) else ''


class PromptBuilder:
    """DSH 侧通过 persona 插件管理人设，桌宠不再构建 system prompt。

    build_messages 只返回用户消息——DSH session API 自身维护对话历史，
    桌宠只需发送最新一条用户输入。
    """

    def __init__(self, characters_root=None):
        self.characters_root = Path(characters_root) if characters_root else None

    def effective_system_prompt(self, settings, character_id, role_prompt=None):
        return ''

    def build_messages(self, settings, character_id, history, user_text, role_prompt=None, now=None):
        return [{'role': 'user', 'content': user_text.strip()}]

    @staticmethod
    def trim_history(history, message_limit, char_limit):
        result = []
        used = 0
        limit = max(100, char_limit)
        for m in reversed(history):
            if result and (len(result) >= max(1, message_limit) or used + len(m.content) > limit):
                break
            if not result and len(m.content) > limit:
                result.append(ChatMessage(m.role, m.content[-limit:], m.created_at, m.message_id))
                break
            result.append(m)
            used += len(m.content)
        return list(reversed(result))