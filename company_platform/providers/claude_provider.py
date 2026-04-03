from __future__ import annotations

import socket
from typing import Any

import requests

from ..models import ProviderConfig
from .base import BaseProvider, ProviderConfigurationError, ProviderNetworkError


class ClaudeProvider(BaseProvider):
    name = "claude"

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
            raise ProviderConfigurationError("ANTHROPIC_API_KEY is not configured")
        if not target_model:
            raise ProviderConfigurationError("CLAUDE_MODEL is not configured")

        payload: dict[str, Any] = {
            "model": target_model,
            "max_tokens": 4096,
            "messages": [
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
            "temperature": temperature,
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = requests.post(
                f"{self.config.base_url.rstrip('/')}/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
                timeout=self.config.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            texts: list[str] = []
            for item in data.get("content", []):
                if item.get("type") == "text" and item.get("text"):
                    texts.append(item["text"])
            return "\n".join(texts).strip()
        except socket.gaierror as exc:
            raise ProviderNetworkError(f"Claude DNS lookup failed: {exc}") from exc
        except requests.exceptions.ConnectionError as exc:
            raise ProviderNetworkError(f"Claude network is unreachable: {exc}") from exc
