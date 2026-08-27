"""应用配置：加载 / 保存本地 config.json。

数据目录：
- 源码运行：项目根目录下的 data/；
- PyInstaller 打包运行：%APPDATA%\\RPsoft（Program Files 下也可写、卸载不丢数据）。
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def is_frozen() -> bool:
    """是否以 PyInstaller 打包后的可执行文件运行。"""
    return bool(getattr(sys, "frozen", False))


def _resolve_data_dir() -> Path:
    """确定数据目录。

    - 源码运行：项目根目录 data/；
    - 打包运行：%APPDATA%\\RPsoft（用户目录，可写；避免 Program Files 只读、
      卸载误删数据）。
    """
    if not is_frozen():
        return _PROJECT_ROOT / "data"
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "RPsoft"
    # 兜底：极少数环境没有 APPDATA 时，退回 exe 目录
    return Path(sys.executable).resolve().parent / "data"


DATA_DIR = _resolve_data_dir()
CHARACTERS_DIR = DATA_DIR / "characters"
CHATS_DIR = DATA_DIR / "chats"
CONFIG_PATH = DATA_DIR / "config.json"


def _migrate_legacy_data() -> None:
    """把旧版「exe 旁 data/」迁移到新的 %APPDATA%\\RPsoft（仅打包运行时、一次）。"""
    if not is_frozen():
        return
    legacy = Path(sys.executable).resolve().parent / "data"
    if legacy.exists() and not DATA_DIR.exists():
        try:
            shutil.copytree(legacy, DATA_DIR)
        except Exception:  # noqa: BLE001 迁移失败不阻塞启动
            pass

DEFAULT_SYSTEM_PROMPT = (
    "你将扮演一个角色，与用户进行沉浸式角色扮演对话。\n"
    "请完全代入下面的角色设定，始终以该角色的身份、口吻与语气回应，不要跳出角色，也不要替用户发言。\n"
    "回答要自然、具体、符合人设，避免长篇说教。\n\n"
    "【角色设定】\n"
    "名称：{name}\n"
    "描述：{description}\n"
    "性格：{personality}\n"
    "世界观 / 背景：{scenario}\n"
    "对话示例：\n{dialogue_examples}\n"
    "额外设定：{system_prompt}\n"
)

DEFAULTS: dict[str, Any] = {
    "api_key": "",
    "base_url": "https://api.deepseek.com/v1",
    "model": "deepseek-v4-flash",
    "temperature": 1.0,
    "max_tokens": 2048,
    "top_p": 1.0,
    "port": 8000,
    "open_browser": True,
    "system_prompt": DEFAULT_SYSTEM_PROMPT,
    "theme": "light",
}


def ensure_dirs() -> None:
    """确保数据目录存在（打包运行时先尝试迁移旧版数据）。"""
    _migrate_legacy_data()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)
    CHATS_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict[str, Any]:
    """读取配置，缺失字段用默认值补齐。"""
    cfg = dict(DEFAULTS)
    if CONFIG_PATH.exists():
        try:
            stored = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(stored, dict):
                cfg.update(stored)
        except (json.JSONDecodeError, OSError):
            pass
    return cfg


def save_config(cfg: dict[str, Any]) -> None:
    """写回配置（会自动创建 data 目录）。"""
    ensure_dirs()
    CONFIG_PATH.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def update_config(patch: dict[str, Any]) -> dict[str, Any]:
    """合并更新配置并保存，返回最新配置。"""
    cfg = load_config()
    for key, value in patch.items():
        if value is not None and key in DEFAULTS:
            cfg[key] = value
    save_config(cfg)
    return cfg
