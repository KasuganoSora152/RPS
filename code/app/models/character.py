"""角色卡数据模型与加载（RPsoft 自带的简洁 JSON 格式）。"""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


class Character(BaseModel):
    """角色卡。id 由文件名决定，不存进文件里。"""

    name: str = "未命名角色"
    description: str = ""            # 描述
    personality: str = ""            # 性格
    scenario: str = ""               # 背景 / 世界观
    greeting: str = ""               # 开场白（第一条消息）
    dialogue_examples: str = ""      # 对话示例
    system_prompt: str = ""          # 额外设定（拼进系统提示词）
    tags: list[str] = Field(default_factory=list)
    locked: bool = False             # 预设角色：不可编辑 / 删除


def _as_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, str):
        return [t.strip() for t in value.split(",") if t.strip()]
    return []


def character_from_dict(raw: dict) -> Character:
    """从扁平 JSON 字典构造角色。"""
    return Character(
        name=raw.get("name") or "未命名角色",
        description=raw.get("description") or "",
        personality=raw.get("personality") or "",
        scenario=raw.get("scenario") or "",
        greeting=raw.get("greeting") or "",
        dialogue_examples=raw.get("dialogue_examples") or "",
        system_prompt=raw.get("system_prompt") or "",
        tags=_as_list(raw.get("tags")),
        locked=bool(raw.get("locked")),
    )


def load_character_file(path: Path) -> Character:
    """从磁盘加载角色卡（.json）。"""
    raw = json.loads(path.read_text(encoding="utf-8"))
    return character_from_dict(raw)
