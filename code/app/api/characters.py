"""角色卡相关 API：列表 / 增删改查 / 导入（JSON）。"""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from app.config import CHARACTERS_DIR, ensure_dirs
from app.core.history import delete_chats_for_character
from app.models.character import Character, character_from_dict, load_character_file
from app.models.schemas import CharacterImport

router = APIRouter(tags=["characters"])


def _slug(name: str) -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", name.strip()).strip("-").lower()
    return slug or "character"


def _card_path(char_id: str) -> Path:
    return CHARACTERS_DIR / f"{char_id}.json"


def _unique_id(base: str) -> str:
    ensure_dirs()
    candidate = base
    index = 2
    while _card_path(candidate).exists():
        candidate = f"{base}-{index}"
        index += 1
    return candidate


def _load_card(char_id: str) -> Character:
    path = _card_path(char_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="角色不存在")
    return load_character_file(path)


def _summary(char_id: str, char: Character) -> dict[str, Any]:
    return {
        "id": char_id,
        "name": char.name,
        "description": char.description[:120],
        "tags": char.tags,
        "locked": char.locked,
    }


def _save(char_id: str, char: Character) -> None:
    ensure_dirs()
    _card_path(char_id).write_text(
        char.model_dump_json(indent=2), encoding="utf-8"
    )


@router.get("/characters")
def list_characters() -> list[dict[str, Any]]:
    ensure_dirs()
    result: list[dict[str, Any]] = []
    for path in sorted(CHARACTERS_DIR.glob("*.json")):
        try:
            result.append(_summary(path.stem, load_character_file(path)))
        except (ValueError, json.JSONDecodeError):
            continue
    return result


@router.post("/characters/import")
def import_character(item: CharacterImport) -> dict[str, Any]:
    ensure_dirs()
    raw = base64.b64decode(item.data_base64)
    char = character_from_dict(json.loads(raw.decode("utf-8")))
    char_id = _unique_id(_slug(char.name))
    _save(char_id, char)
    return _summary(char_id, char)


@router.post("/characters")
def create_character(data: Character) -> dict[str, Any]:
    ensure_dirs()
    char_id = _unique_id(_slug(data.name))
    _save(char_id, data)
    return _summary(char_id, data)


@router.get("/characters/{char_id}")
def get_character(char_id: str) -> Character:
    return _load_card(char_id)


@router.put("/characters/{char_id}")
def update_character(char_id: str, data: Character) -> dict[str, Any]:
    existing = _load_card(char_id)
    if existing.locked:
        raise HTTPException(status_code=403, detail="预设角色不可编辑")
    _save(char_id, data)
    return _summary(char_id, data)


@router.delete("/characters/{char_id}")
def delete_character(char_id: str) -> dict[str, Any]:
    card = _load_card(char_id)
    if card.locked:
        raise HTTPException(status_code=403, detail="预设角色不可删除")
    _card_path(char_id).unlink()
    deleted_chats = delete_chats_for_character(char_id)
    return {"ok": True, "deleted_chats": deleted_chats}
