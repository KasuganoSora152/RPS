"""根据角色卡构造系统提示词与消息列表。"""
from __future__ import annotations

from typing import Any

from app.models.character import Character


def build_system_prompt(char: Character, template: str) -> str:
    """把角色字段填入系统提示词模板。"""
    fields = {
        "name": char.name,
        "description": char.description or "（无）",
        "personality": char.personality or "（无）",
        "scenario": char.scenario or "（无）",
        "dialogue_examples": char.dialogue_examples or "（无）",
        "system_prompt": char.system_prompt or "（无）",
    }
    try:
        return template.format(**fields)
    except (KeyError, IndexError, ValueError):
        # 模板里若有未知占位符，原样返回，避免崩溃
        return template


def build_messages(
    char: Character,
    history: list[dict[str, Any]],
    user_text: str,
    template: str,
) -> list[dict[str, str]]:
    """组装完整消息列表：系统提示 + 历史对话 + 本次用户输入。"""
    messages: list[dict[str, str]] = [
        {"role": "system", "content": build_system_prompt(char, template)}
    ]
    for msg in history:
        role = msg.get("role")
        if role in ("user", "assistant"):
            messages.append({"role": role, "content": str(msg.get("content", ""))})
    messages.append({"role": "user", "content": user_text})
    return messages
