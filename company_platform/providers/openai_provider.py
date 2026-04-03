from __future__ import annotations

from typing import Any

import requests

from ..models import ProviderConfig
from .base import BaseProvider


class OpenAIProvider(BaseProvider):
    name = "openai"

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
            raise ValueError("OPENAI_API_KEY is not configured")
        if not target_model:
            raise ValueError("OPENAI_MODEL is not configured")

        payload: dict[str, Any] = {
            "model": target_model,
            "input": user_prompt,
            "temperature": temperature,
        }
        if system_prompt:
            payload["instructions"] = system_prompt

        response = requests.post(
            f"{self.config.base_url.rstrip('/')}/responses",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("output_text"):
            return data["output_text"].strip()
        return _extract_output_text(data)


def _extract_output_text(payload: dict[str, Any]) -> str:
    texts: list[str] = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if text:
                texts.append(text)
    return "\n".join(texts).strip()
