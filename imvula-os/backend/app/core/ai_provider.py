"""
AI provider abstraction.

Swappable by changing AI_PROVIDER in .env:
  mock      (default) — deterministic, no API key, zero cost
  deepseek  — real API call, requires DEEPSEEK_API_KEY

Adding a new provider = adding a new subclass of AIProvider.
The rest of the codebase never needs to know which provider is active.
"""
from abc import ABC, abstractmethod

import httpx

from app.core.config import settings


class AIProviderError(Exception):
    """Raised when a provider fails to return a valid response."""


class AIProvider(ABC):
    """Every provider must implement this interface."""
    name: str = "base"

    @abstractmethod
    async def complete(self, prompt: str, max_tokens: int = 512) -> str:
        ...


class MockProvider(AIProvider):
    """Deterministic fake AI. No network calls, no API key, no cost."""
    name = "mock"

    async def complete(self, prompt: str, max_tokens: int = 512) -> str:
        snippet = prompt.strip().replace("\n", " ")[:80]
        return f"[mock-ai] Received: {snippet}"


class DeepSeekProvider(AIProvider):
    """Real DeepSeek API. Only used when AI_PROVIDER=deepseek."""
    name = "deepseek"
    endpoint = "https://api.deepseek.com/v1/chat/completions"

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        if not api_key:
            raise AIProviderError(
                "DEEPSEEK_API_KEY is not set but AI_PROVIDER=deepseek"
            )
        self.api_key = api_key
        self.model = model

    async def complete(self, prompt: str, max_tokens: int = 512) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(self.endpoint, json=body, headers=headers)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as e:
            raise AIProviderError(f"DeepSeek HTTP error: {e}") from e

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise AIProviderError(f"Unexpected DeepSeek response shape: {data}") from e


def get_provider() -> AIProvider:
    """Factory based on settings. Defaults to mock — safe by default."""
    name = settings.ai_provider.lower().strip()
    if name == "deepseek":
        return DeepSeekProvider(settings.deepseek_api_key, settings.deepseek_model)
    return MockProvider()
