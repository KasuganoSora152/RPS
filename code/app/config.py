"""应用配置：加载 / 保存本地 data/config.json。

支持两种运行方式：
- 源码运行：数据目录在项目根目录下的 data/；
- PyInstaller 打包运行：数据目录在可执行文件旁的 data/（可写、持久）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def is_frozen() -> bool:
    """是否以 PyInstaller 打包后的可执行文件运行。"""
    return bool(getattr(sys, "frozen", False))


if is_frozen():
    # 打包运行：数据目录放在可执行文件旁边（不能放在临时解包目录里，否则退出会被清空）
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = _PROJECT_ROOT

DATA_DIR = BASE_DIR / "data"
CHARACTERS_DIR = DATA_DIR / "characters"
CHATS_DIR = DATA_DIR / "chats"
CONFIG_PATH = DATA_DIR / "config.json"

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
    """确保数据目录存在。"""
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
