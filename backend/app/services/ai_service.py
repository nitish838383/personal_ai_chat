"""
AI provider abstraction layer.
Supports OpenAI-compatible APIs. Can be extended for Gemini, Ollama, etc.
The AI model itself never touches the database or external APIs directly.
"""

from typing import Any, AsyncGenerator, Optional

import httpx

from app.core.config import settings


class AIService:
    """Thin abstraction over chat-completions and embeddings."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = (base_url or settings.OPENAI_BASE_URL).rstrip("/")
        self.model = model or settings.DEFAULT_MODEL
        self.embedding_model = settings.EMBEDDING_MODEL

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def chat(
        self,
        messages: list[dict[str, str]],
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Non-streaming chat completion.
        Returns the full response dict from the provider.
        """
        if not self.api_key:
            # Graceful fallback when no key is configured
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": (
                                "AI provider is not configured. "
                                "Please set OPENAI_API_KEY in the backend .env file."
                            ),
                        }
                    }
                ]
            }

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """Streaming chat completion (yields content deltas)."""
        if not self.api_key:
            yield "AI provider is not configured. Please set OPENAI_API_KEY in the backend .env file."
            return

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break
                    try:
                        import json
                        chunk = json.loads(data)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            yield content
                    except Exception:
                        continue

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Create embeddings for a list of texts."""
        if not self.api_key:
            # Return zero vectors as placeholder
            return [[0.0] * 1536 for _ in texts]

        payload = {
            "model": self.embedding_model,
            "input": texts,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/embeddings",
                headers=self._headers(),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data["data"]]


# Singleton-style helper
def get_ai_service() -> AIService:
    return AIService()
