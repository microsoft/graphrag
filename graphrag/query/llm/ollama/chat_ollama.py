# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Chat-based Ollama LLM implementation."""
from typing import Any, AsyncGenerator, Generator

from tenacity import (
    AsyncRetrying,
    RetryError,
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from graphrag.callbacks.llm_callbacks import BaseLLMCallback
from graphrag.llm import OllamaConfiguration, create_ollama_client
from graphrag.query.llm.base import BaseLLM


class ChatOllama(BaseLLM):
    """Wrapper for Ollama ChatCompletion models."""

    def __init__(self, configuration: OllamaConfiguration):
        self.configuration = configuration
        self.sync_client = create_ollama_client(configuration, sync=True)
        self.async_client = create_ollama_client(configuration)

    def generate(
        self,
        messages: str | list[Any],
        streaming: bool = True,
        callbacks: list[BaseLLMCallback] | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate a response."""
        response = self.sync_client.chat(
            messages,
            **self.configuration.get_chat_cache_args(),
        )
        return response["message"]["content"]

    def stream_generate(
        self,
        messages: str | list[Any],
        callbacks: list[BaseLLMCallback] | None = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """Generate a response with streaming."""

    async def agenerate(
        self,
        messages: str | list[Any],
        streaming: bool = True,
        callbacks: list[BaseLLMCallback] | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate a response asynchronously."""
        """Generate text asynchronously."""
        try:
            retryer = AsyncRetrying(
                stop=stop_after_attempt(self.configuration.max_retries),
                wait=wait_exponential_jitter(max=10),
                reraise=True,
                retry=retry_if_exception_type(Exception),  # type: ignore
            )
            async for attempt in retryer:
                with attempt:
                    response = await self.async_client.chat(
                        messages=messages,
                        **{
                            **self.configuration.get_chat_cache_args(),
                            "stream": False,
                        }
                    )
                    return response["message"]["content"]
        except Exception as e:
            raise e

    async def astream_generate(
        self,
        messages: str | list[Any],
        callbacks: list[BaseLLMCallback] | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Generate a response asynchronously with streaming."""
        ...

