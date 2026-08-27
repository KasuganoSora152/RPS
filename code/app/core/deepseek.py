"""DeepSeek OpenAI 兼容接口客户端（流式对话 + 连接测试）。"""
from __future__ import annotations

import json
from typing import Any, AsyncIterator

import httpx


class DeepSeekError(Exception):
    """DeepSeek 接口调用失败。"""


class DeepSeekClient:
    def __init__(self, config: dict[str, Any]):
        self.config = config

    def _endpoint(self, path: str) -> str:
        base = (self.config.get("base_url") or "https://api.deepseek.com/v1").rstrip("/")
        # 容错：若用户直接填了 /chat/completions 结尾的地址，则去掉该段
        if base.endswith("/chat/completions"):
            base = base[: -len("/chat/completions")]
        return f"{base}{path}"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.get('api_key', '')}",
            "Content-Type": "application/json",
        }

    async def stream_chat(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        """流式调用 chat/completions，逐段产出增量文本。"""
        payload = {
            "model": self.config.get("model", "deepseek-v4-flash"),
            "messages": messages,
            "stream": True,
            "temperature": self.config.get("temperature", 1.0),
            "max_tokens": self.config.get("max_tokens", 2048),
            "top_p": self.config.get("top_p", 1.0),
        }
        url = self._endpoint("/chat/completions")
        timeout = httpx.Timeout(connect=15.0, read=300.0, write=30.0, pool=15.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST", url, json=payload, headers=self._headers()
            ) as resp:
                if resp.status_code >= 400:
                    body = (await resp.aread()).decode("utf-8", "replace")
                    raise DeepSeekError(f"DeepSeek 接口返回 {resp.status_code}: {body[:500]}")
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[len("data:") :].strip()
                    if data == "[DONE]":
                        break
                    try:
                        obj = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    choices = obj.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    piece = delta.get("content")
                    if piece:
                        yield piece

    async def test(self) -> tuple[bool, str, list[str]]:
        """调用 /models 校验 API Key，返回 (是否成功, 提示, 可用模型列表)。"""
        url = self._endpoint("/models")
        timeout = httpx.Timeout(connect=15.0, read=30.0, write=15.0, pool=15.0)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(url, headers=self._headers())
                if resp.status_code >= 400:
                    return False, f"接口返回 {resp.status_code}: {resp.text[:300]}", []
                data = resp.json()
                models = [m.get("id", "") for m in data.get("data", [])]
                return True, "连接成功", models
        except httpx.HTTPError as exc:
            return False, f"网络错误: {exc}", []
