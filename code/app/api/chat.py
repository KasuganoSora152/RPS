"""聊天会话与消息流式接口。"""
from __future__ import annotations

import json
from typing import Any, AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.api.characters import _load_card
from app.config import load_config
from app.core.deepseek import DeepSeekClient, DeepSeekError
from app.core.history import (
    append_message,
    create_chat,
    delete_chat,
    get_chat,
    list_chats,
    rename_chat,
)
from app.core.prompt import build_messages
from app.models.schemas import ChatCreate, ChatRename, MessageIn

router = APIRouter(tags=["chat"])


@router.get("/chats")
def chats_list() -> list[dict[str, Any]]:
    return list_chats()


@router.post("/chats")
def chats_create(body: ChatCreate) -> dict[str, Any]:
    card = _load_card(body.character_id)
    return create_chat(body.character_id, card.name, card.greeting, body.name)


@router.get("/chats/{chat_id}")
def chats_get(chat_id: str) -> dict[str, Any]:
    chat = get_chat(chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return chat


@router.delete("/chats/{chat_id}")
def chats_delete(chat_id: str) -> dict[str, Any]:
    if not delete_chat(chat_id):
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"ok": True}


@router.patch("/chats/{chat_id}")
def chats_rename(chat_id: str, body: ChatRename) -> dict[str, Any]:
    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="会话名称不能为空")
    chat = rename_chat(chat_id, title)
    if chat is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return chat


@router.post("/chats/{chat_id}/messages")
async def chats_send(chat_id: str, body: MessageIn) -> StreamingResponse:
    """发送消息并以 SSE 流式返回助手回复。"""
    chat = get_chat(chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    card = _load_card(chat["character_id"])
    cfg = load_config()

    if not cfg.get("api_key"):
        raise HTTPException(status_code=400, detail="尚未配置 DeepSeek API Key")

    user_text = body.content.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="消息不能为空")

    # 先落盘用户消息；历史快照用于拼装上下文（避免重复追加用户消息）
    history_before = list(chat["messages"])
    append_message(chat, "user", user_text)

    def sse(event: dict[str, Any]) -> str:
        return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    async def gen() -> AsyncIterator[str]:
        collected: list[str] = []
        client = DeepSeekClient(cfg)
        messages = build_messages(
            card, history_before, user_text, cfg.get("system_prompt", "")
        )
        try:
            async for piece in client.stream_chat(messages):
                collected.append(piece)
                yield sse({"delta": piece})
        except DeepSeekError as exc:
            yield sse({"error": str(exc)})
            return
        except Exception as exc:  # noqa: BLE001
            yield sse({"error": f"生成失败: {exc}"})
            return

        full = "".join(collected)
        if full:
            append_message(chat, "assistant", full)
        yield sse({"done": True, "message": {"role": "assistant", "content": full}})

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
