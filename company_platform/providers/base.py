from __future__ import annotations

from abc import ABC, abstractmethod


class ProviderError(RuntimeError):
    """Base provider error."""


class ProviderNetworkError(ProviderError):
    """Raised when the provider cannot be reached over the network."""


class ProviderConfigurationError(ProviderError):
    """Raised when required provider settings are missing."""


class BaseProvider(ABC):
    name: str

    @abstractmethod
    def generate(
        self,
        user_prompt: str,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        raise NotImplementedError
