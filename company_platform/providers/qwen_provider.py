from __future__ import annotations

from typing import Any

import requests

from ..models import ProviderConfig
from .base import BaseProvider


class QwenProvider(BaseProvider):
    name = "qwen"

    def __init__(self, config: ProviderConfig):
        self.config = config

    def generate(
        self,
        user_prompt: str,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        api_key = self.config.api_key
        target_model = model or self.config.model
        if not api_key:
            raise ValueError("QWEN_API_KEY is not configured")
        if not target_model:
            raise ValueError("QWEN_MODEL is not configured")

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        payload: dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
        }
        response = requests.post(
            f"{self.config.base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            return ""
        message = choices[0].get("message", {})
        return str(message.get("content", "")).strip()
