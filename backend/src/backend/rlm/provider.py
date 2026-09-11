from __future__ import annotations

from abc import ABC, abstractmethod

from openai import AsyncOpenAI

from .models import LLMMessage, LLMResponse


class LLMProvider(ABC):

    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
    ) -> LLMResponse:
        raise NotImplementedError


class OpenAICompatibleProvider(LLMProvider):
    """
    Works with OpenAI-compatible APIs.

    Examples:
        OpenAI
        LM Studio
        Ollama OpenAI-compatible endpoint
        vLLM
        LiteLLM-compatible endpoints
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = 120,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self._client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout,
        )

    async def generate(
        self,
        messages: list[LLMMessage],
    ) -> LLMResponse:

        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": message.role,
                    "content": message.content,
                }
                for message in messages
            ],
            temperature=0,
        )

        choice = response.choices[0]
        usage = (
            response.usage.model_dump()
            if response.usage is not None
            else {}
        )

        return LLMResponse(
            content=choice.message.content or "",
            usage=usage,
        )
