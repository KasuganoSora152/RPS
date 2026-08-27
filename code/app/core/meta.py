"""排序与置顶的元数据存储（data/meta.json）。"""
from __future__ import annotations

import json
from typing import Any

from app.config import DATA_DIR, ensure_dirs

META_PATH = DATA_DIR / "meta.json"

_DEFAULTS: dict[str, list[str]] = {
    "character_order": [],      # 角色显示顺序（不含置顶项）
    "pinned_characters": [],    # 置顶角色（按顺序）
    "chat_order": [],           # 会话显示顺序（不含置顶项）
    "pinned_chats": [],         # 置顶会话（按顺序）
}


def load_meta() -> dict[str, Any]:
    ensure_dirs()
    meta: dict[str, Any] = {k: list(v) for k, v in _DEFAULTS.items()}
    if META_PATH.exists():
        try:
            stored = json.loads(META_PATH.read_text(encoding="utf-8"))
            if isinstance(stored, dict):
                for key in _DEFAULTS:
                    if isinstance(stored.get(key), list):
                        meta[key] = stored[key]
        except (json.JSONDecodeError, OSError):
            pass
    return meta


def save_meta(meta: dict[str, Any]) -> None:
    ensure_dirs()
    META_PATH.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def update_meta(patch: dict[str, Any]) -> dict[str, Any]:
    meta = load_meta()
    for key in _DEFAULTS:
        if key in patch and isinstance(patch[key], list):
            meta[key] = patch[key]
    save_meta(meta)
    return meta
