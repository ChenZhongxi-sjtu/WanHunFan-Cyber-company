from __future__ import annotations

import socket

from ..models import ProviderConfig
from .base import BaseProvider, ProviderConfigurationError, ProviderNetworkError


class GeminiProvider(BaseProvider):
    name = "gemini"

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
            raise ProviderConfigurationError("GEMINI_API_KEY is not configured")
        if not target_model:
            raise ProviderConfigurationError("GEMINI_MODEL is not configured")

        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise ProviderConfigurationError(
                "Gemini provider requires google-genai. Install it with: pip install google-genai"
            ) from exc

        http_options = None
        if self.config.base_url:
            try:
                http_options = types.HttpOptions(
                    base_url=self.config.base_url,
                    timeout=self.config.timeout_seconds * 1000,
                )
            except TypeError:
                http_options = None

        try:
            client = genai.Client(
                api_key=api_key,
                http_options=http_options,
            )
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=user_prompt),
                    ],
                )
            ]
            config_kwargs: dict[str, object] = {
                "temperature": temperature,
            }
            if system_prompt:
                config_kwargs["system_instruction"] = system_prompt
            if target_model.startswith("gemini-3.1"):
                config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level="HIGH")

            generate_content_config = types.GenerateContentConfig(**config_kwargs)
            texts: list[str] = []
            for chunk in client.models.generate_content_stream(
                model=target_model,
                contents=contents,
                config=generate_content_config,
            ):
                if chunk.text:
                    texts.append(chunk.text)
            return "".join(texts).strip()
        except socket.gaierror as exc:
            raise ProviderNetworkError(f"Gemini DNS lookup failed: {exc}") from exc
        except OSError as exc:
            lowered = str(exc).lower()
            if "network is unreachable" in lowered or "failed to establish a new connection" in lowered:
                raise ProviderNetworkError(f"Gemini network is unreachable: {exc}") from exc
            raise
        except Exception as exc:
            lowered = str(exc).lower()
            if "network is unreachable" in lowered or "failed to establish a new connection" in lowered:
                raise ProviderNetworkError(f"Gemini network is unreachable: {exc}") from exc
            raise
