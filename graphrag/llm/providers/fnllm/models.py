# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing fnllm model provider definitions."""

from fnllm.openai import (
    create_openai_chat_llm,
    create_openai_client,
    create_openai_embeddings_llm,
)
from fnllm.types import ChatLLM as FNLLMChatLLM
from fnllm.types import EmbeddingsLLM as FNLLMEmbeddingLLM

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.language_model_config import (
    LanguageModelConfig,
)
from graphrag.llm.providers.fnllm.events import FNLLMEvents
from graphrag.llm.providers.fnllm.utils import (
    _create_cache,
    _create_error_handler,
    _create_openai_config,
)
from graphrag.llm.response.base import BaseLLMOutput, BaseLLMResponse, LLMResponse


class OpenAIChatFNLLM:
    """An OpenAI Chat LLM provider using the fnllm library."""

    llm: FNLLMChatLLM

    def __init__(
        self,
        *,
        name: str,
        config: LanguageModelConfig,
        callbacks: WorkflowCallbacks,
        cache: PipelineCache | None,
    ) -> None:
        llm_config = _create_openai_config(config, False)
        error_handler = _create_error_handler(callbacks)
        llm_cache = _create_cache(cache, name)
        client = create_openai_client(llm_config)
        self.llm = create_openai_chat_llm(
            llm_config,
            client=client,
            cache=llm_cache,
            events=FNLLMEvents(error_handler),
        )

    async def chat(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Chat with the LLM using the given prompt.

        Args:
            prompt: The prompt to chat with.
            kwargs: Additional arguments to pass to the LLM.

        Returns
        -------
            The response from the LLM.
        """
        response = await self.llm(prompt, **kwargs)
        return BaseLLMResponse(
            output=BaseLLMOutput(content=response.output.content),
            parsed_response=response.parsed_json,
            history=response.history,
            cache_hit=response.cache_hit,
            tool_calls=response.tool_calls,
            metrics=response.metrics,
        )


class OpenAIEmbeddingFNLLM:
    """An OpenAI Embedding LLM provider using the fnllm library."""

    llm: FNLLMEmbeddingLLM

    def __init__(
        self,
        *,
        name: str,
        config: LanguageModelConfig,
        callbacks: WorkflowCallbacks,
        cache: PipelineCache | None,
    ) -> None:
        llm_config = _create_openai_config(config, False)
        error_handler = _create_error_handler(callbacks)
        llm_cache = _create_cache(cache, name)
        client = create_openai_client(llm_config)
        self.llm = create_openai_embeddings_llm(
            llm_config,
            client=client,
            cache=llm_cache,
            events=FNLLMEvents(error_handler),
        )

    async def embed(self, text: str | list[str], **kwargs) -> list[list[float]]:
        """
        Embed the given text using the LLM.

        Args:
            text: The text to embed.
            kwargs: Additional arguments to pass to the LLM.

        Returns
        -------
            The embeddings of the text.
        """
        response = await self.llm(text, **kwargs)
        if response.output.embeddings is None:
            msg = "No embeddings found in response"
            raise ValueError(msg)
        embeddings: list[list[float]] = response.output.embeddings
        return embeddings


class AzureOpenAIChatFNLLM:
    """An Azure OpenAI Chat LLM provider using the fnllm library."""

    llm: FNLLMChatLLM

    def __init__(
        self,
        *,
        name: str,
        config: LanguageModelConfig,
        callbacks: WorkflowCallbacks,
        cache: PipelineCache | None,
    ) -> None:
        llm_config = _create_openai_config(config, True)
        error_handler = _create_error_handler(callbacks)
        llm_cache = _create_cache(cache, name)
        client = create_openai_client(llm_config)
        self.llm = create_openai_chat_llm(
            llm_config,
            client=client,
            cache=llm_cache,
            events=FNLLMEvents(error_handler),
        )

    async def chat(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Chat with the LLM using the given prompt.

        Args:
            prompt: The prompt to chat with.
            kwargs: Additional arguments to pass to the LLM.

        Returns
        -------
            The response from the LLM.
        """
        response = await self.llm(prompt, **kwargs)
        return BaseLLMResponse(
            output=BaseLLMOutput(content=response.output.content),
            parsed_response=response.parsed_json,
            history=response.history,
            cache_hit=response.cache_hit,
            tool_calls=response.tool_calls,
            metrics=response.metrics,
        )


class AzureOpenAIEmbeddingFNLLM:
    """An Azure OpenAI Embedding LLM provider using the fnllm library."""

    llm: FNLLMEmbeddingLLM

    def __init__(
        self,
        *,
        name: str,
        config: LanguageModelConfig,
        callbacks: WorkflowCallbacks,
        cache: PipelineCache | None,
    ) -> None:
        llm_config = _create_openai_config(config, True)
        error_handler = _create_error_handler(callbacks)
        llm_cache = _create_cache(cache, name)
        client = create_openai_client(llm_config)
        self.llm = create_openai_embeddings_llm(
            llm_config,
            client=client,
            cache=llm_cache,
            events=FNLLMEvents(error_handler),
        )

    async def embed(self, text: str | list[str], **kwargs) -> list[list[float]]:
        """
        Embed the given text using the LLM.

        Args:
            text: The text to embed.
            kwargs: Additional arguments to pass to the LLM.

        Returns
        -------
            The embeddings of the text.
        """
        response = await self.llm(text, **kwargs)
        if response.output.embeddings is None:
            msg = "No embeddings found in response"
            raise ValueError(msg)
        embeddings: list[list[float]] = response.output.embeddings
        return embeddings
