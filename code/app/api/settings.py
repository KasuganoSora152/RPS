"""设置与连接测试 API。"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.config import load_config, update_config
from app.core.deepseek import DeepSeekClient
from app.models.schemas import SettingsUpdate

router = APIRouter(tags=["settings"])


@router.get("/settings")
def get_settings() -> dict[str, Any]:
    cfg = load_config()
    key = cfg.get("api_key", "")
    cfg["api_key_masked"] = (
        f"{key[:4]}****{key[-4:]}" if len(key) > 8 else ("已设置" if key else "未设置")
    )
    return cfg


@router.put("/settings")
def put_settings(body: SettingsUpdate) -> dict[str, Any]:
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    return update_config(patch)


@router.post("/settings/test")
async def test_settings() -> dict[str, Any]:
    cfg = load_config()
    if not cfg.get("api_key"):
        return {"ok": False, "message": "尚未填写 API Key", "models": []}
    client = DeepSeekClient(cfg)
    ok, msg, models = await client.test()
    return {"ok": ok, "message": msg, "models": models}
