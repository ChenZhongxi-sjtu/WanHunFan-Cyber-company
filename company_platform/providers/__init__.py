from __future__ import annotations

from ..models import CompanySettings
from .base import BaseProvider
from .claude_provider import ClaudeProvider
from .gemini_provider import GeminiProvider
from .mock import MockProvider
from .openai_provider import OpenAIProvider
from .qwen_provider import QwenProvider


def build_provider(settings: CompanySettings, provider_name: str | None = None) -> BaseProvider:
    name = (provider_name or settings.default_provider).lower()
    config = settings.providers.get(name)
    if name == "mock":
        return MockProvider()
    if not config:
        raise ValueError(f"Unsupported provider: {name}")
    if name == "openai":
        return OpenAIProvider(config)
    if name == "gemini":
        return GeminiProvider(config)
    if name == "qwen":
        return QwenProvider(config)
    if name == "claude":
        return ClaudeProvider(config)
    raise ValueError(f"Unsupported provider: {name}")
