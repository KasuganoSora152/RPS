"""API 请求 / 响应体模型。"""
from __future__ import annotations

from pydantic import BaseModel


class MessageIn(BaseModel):
    content: str


class ChatCreate(BaseModel):
    character_id: str
    name: str | None = None  # 可选会话标题


class ChatRename(BaseModel):
    title: str


class SettingsUpdate(BaseModel):
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    system_prompt: str | None = None
    theme: str | None = None


class CharacterImport(BaseModel):
    filename: str
    data_base64: str  # 角色卡 JSON 文件的 base64
