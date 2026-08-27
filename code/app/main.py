"""FastAPI 应用入口与静态资源挂载。"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import characters, chat, meta, settings
from app.config import ensure_dirs

WEB_DIR = Path(__file__).resolve().parent / "web"


def create_app() -> FastAPI:
    ensure_dirs()
    app = FastAPI(
        title="RPS",
        version="0.1.0",
        description="本地角色扮演对话应用（DeepSeek API）",
    )

    app.include_router(characters.router, prefix="/api")
    app.include_router(chat.router, prefix="/api")
    app.include_router(settings.router, prefix="/api")
    app.include_router(meta.router, prefix="/api")

    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
    return app


app = create_app()
