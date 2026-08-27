"""聊天记录存储：每个会话一个 JSON 文件（零数据库依赖）。"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

from app.config import CHATS_DIR, ensure_dirs


def _chat_path(chat_id: str) -> Path:
    return CHATS_DIR / f"{chat_id}.json"


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def create_chat(
    character_id: str,
    character_name: str,
    greeting: str,
    title: str | None = None,
) -> dict[str, Any]:
    """新建会话；若角色有开场白，则作为第一条助手消息写入。"""
    ensure_dirs()
    now = time.time()
    chat_title = title.strip() if title and title.strip() else None
    if chat_title is None:
        # 自动命名：角色名_会话_N，按该角色已有会话数递增并保证不重名
        existing_titles: set[str] = set()
        count = 0
        for path in CHATS_DIR.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if data.get("character_id") == character_id:
                    count += 1
                    existing_titles.add(data.get("title", ""))
            except (json.JSONDecodeError, OSError):
                continue
        n = count + 1
        chat_title = f"{character_name}_会话_{n}"
        while chat_title in existing_titles:
            n += 1
            chat_title = f"{character_name}_会话_{n}"
    chat: dict[str, Any] = {
        "id": _new_id(),
        "character_id": character_id,
        "character_name": character_name,
        "title": chat_title,
        "created_at": now,
        "updated_at": now,
        "messages": [],
    }
    if greeting:
        chat["messages"].append({"role": "assistant", "content": greeting, "ts": now})
    _chat_path(chat["id"]).write_text(
        json.dumps(chat, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return chat


def list_chats() -> list[dict[str, Any]]:
    """按最近更新时间倒序返回所有会话。"""
    ensure_dirs()
    chats: list[dict[str, Any]] = []
    for path in sorted(
        CHATS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True
    ):
        try:
            chats.append(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return chats


def get_chat(chat_id: str) -> dict[str, Any] | None:
    path = _chat_path(chat_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_chat(chat: dict[str, Any]) -> None:
    ensure_dirs()
    _chat_path(chat["id"]).write_text(
        json.dumps(chat, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def append_message(chat: dict[str, Any], role: str, content: str) -> None:
    chat["messages"].append({"role": role, "content": content, "ts": time.time()})
    chat["updated_at"] = time.time()
    save_chat(chat)


def delete_chat(chat_id: str) -> bool:
    path = _chat_path(chat_id)
    if path.exists():
        path.unlink()
        return True
    return False


def delete_chats_for_character(character_id: str) -> int:
    """删除某个角色的所有会话，返回删除数量。"""
    ensure_dirs()
    deleted = 0
    for path in CHATS_DIR.glob("*.json"):
        try:
            chat = json.loads(path.read_text(encoding="utf-8"))
            if chat.get("character_id") == character_id:
                path.unlink()
                deleted += 1
        except (json.JSONDecodeError, OSError):
            continue
    return deleted


def rename_chat(chat_id: str, title: str) -> dict[str, Any] | None:
    """重命名会话，返回更新后的会话；不存在返回 None。"""
    chat = get_chat(chat_id)
    if chat is None:
        return None
    chat["title"] = title
    chat["updated_at"] = time.time()
    save_chat(chat)
    return chat
