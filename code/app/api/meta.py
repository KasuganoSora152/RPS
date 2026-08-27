"""排序 / 置顶元数据 API。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.meta import load_meta, update_meta

router = APIRouter(tags=["meta"])


class MetaUpdate(BaseModel):
    character_order: list[str] | None = None
    pinned_characters: list[str] | None = None
    chat_order: list[str] | None = None
    pinned_chats: list[str] | None = None


@router.get("/meta")
def get_meta() -> dict[str, Any]:
    return load_meta()


@router.put("/meta")
def put_meta(body: MetaUpdate) -> dict[str, Any]:
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    return update_meta(patch)
