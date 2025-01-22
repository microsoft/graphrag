# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Load llm utilities."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from fnllm import ChatLLM, EmbeddingsLLM, JsonStrategy, LLMEvents
from fnllm.caching import Cache as LLMCache
from fnllm.openai import (
    AzureOpenAIConfig,
    OpenAIConfig,
    PublicOpenAIConfig,
    create_openai_chat_llm,
    create_openai_client,
    create_openai_embeddings_llm,
)
from fnllm.openai.types.chat.parameters import OpenAIChatParameters

import graphrag.config.defaults as defs
from graphrag.config.enums import LLMType
from graphrag.config.models.language_model_config import (
    LanguageModelConfig,  # noqa: TC001
)
from graphrag.index.llm.manager import ChatLLMSingleton, EmbeddingsLLMSingleton

from .mock_llm import MockChatLLM

if TYPE_CHECKING:
    from graphrag.cache.pipeline_cache import PipelineCache
    from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
    from graphrag.index.typing import ErrorHandlerFn

log = logging.getLogger(__name__)


class GraphRagLLMEvents(LLMEvents):
    """LLM events handler that calls the error handler."""

    def __init__(self, on_error: ErrorHandlerFn):
        self._on_error = on_error

    async def on_error(
        self,
        error: BaseException | None,
        traceback: str | None = None,
        arguments: dict[str, Any] | None = None,
    ) -> None:
        """Handle an fnllm error."""
        self._on_error(error, traceback, arguments)


class GraphRagLLMCache(LLMCache):
    """A cache for the pipeline."""

    def __init__(self, cache: PipelineCache):
        self._cache = cache

    async def has(self, key: str) -> bool:
        """Check if the cache has a value."""
        return await self._cache.has(key)

    async def get(self, key: str) -> Any | None:
        """Retrieve a value from the cache."""
        return await self._cache.get(key)

    async def set(
        self, key: str, value: Any, metadata: dict[str, Any] | None = None
    ) -> None:
        """Write a value into the cache."""
        await self._cache.set(key, value, metadata)

    async def remove(self, key: str) -> None:
        """Remove a value from the cache."""
        await self._cache.delete(key)

    async def clear(self) -> None:
        """Clear the cache."""
        await self._cache.clear()

    def child(self, key: str):
        """Create a child cache."""
        child_cache = self._cache.child(key)
        return GraphRagLLMCache(child_cache)


def create_cache(cache: PipelineCache | None, name: str) -> LLMCache | None:
    """Create an LLM cache from a pipeline cache."""
    if cache is None:
        return None
    return GraphRagLLMCache(cache).child(name)


def load_llm(
    name: str,
    config: LanguageModelConfig,
    *,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache | None,
    chat_only=False,
) -> ChatLLM:
    """Load the LLM for the entity extraction chain."""
    singleton_llm = ChatLLMSingleton().get_llm(name)
    if singleton_llm is not None:
        return singleton_llm

    on_error = _create_error_handler(callbacks)
    llm_type = config.type

    if llm_type in loaders:
        if chat_only and not loaders[llm_type]["chat"]:
            msg = f"LLM type {llm_type} does not support chat"
            raise ValueError(msg)

        loader = loaders[llm_type]
        llm_instance = loader["load"](on_error, create_cache(cache, name), config)
        ChatLLMSingleton().set_llm(name, llm_instance)
        return llm_instance

    msg = f"Unknown LLM type {llm_type}"
    raise ValueError(msg)


def load_llm_embeddings(
    name: str,
    llm_config: LanguageModelConfig,
    *,
    callbacks: WorkflowCallbacks,
    cache: PipelineCache | None,
    chat_only=False,
) -> EmbeddingsLLM:
    """Load the LLM for the entity extraction chain."""
    singleton_llm = EmbeddingsLLMSingleton().get_llm(name)
    if singleton_llm is not None:
        return singleton_llm

    on_error = _create_error_handler(callbacks)
    llm_type = llm_config.type
    if llm_type in loaders:
        if chat_only and not loaders[llm_type]["chat"]:
            msg = f"LLM type {llm_type} does not support chat"
            raise ValueError(msg)
        llm_instance = loaders[llm_type]["load"](
            on_error, create_cache(cache, name), llm_config or {}
        )
        EmbeddingsLLMSingleton().set_llm(name, llm_instance)
        return llm_instance

    msg = f"Unknown LLM type {llm_type}"
    raise ValueError(msg)


def _create_error_handler(callbacks: WorkflowCallbacks) -> ErrorHandlerFn:
    def on_error(
        error: BaseException | None = None,
        stack: str | None = None,
        details: dict | None = None,
    ) -> None:
        callbacks.error("Error Invoking LLM", error, stack, details)

    return on_error


def _load_openai_chat_llm(
    on_error: ErrorHandlerFn,
    cache: LLMCache,
    config: LanguageModelConfig,
    azure=False,
):
    return _create_openai_chat_llm(
        _create_openai_config(config, azure),
        on_error,
        cache,
    )


def _load_openai_embeddings_llm(
    on_error: ErrorHandlerFn,
    cache: LLMCache,
    config: LanguageModelConfig,
    azure=False,
):
    return _create_openai_embeddings_llm(
        _create_openai_config(config, azure),
        on_error,
        cache,
    )


def _create_openai_config(config: LanguageModelConfig, azure: bool) -> OpenAIConfig:
    encoding_model = config.encoding_model
    json_strategy = (
        JsonStrategy.VALID if config.model_supports_json else JsonStrategy.LOOSE
    )
    chat_parameters = OpenAIChatParameters(
        frequency_penalty=config.frequency_penalty,
        presence_penalty=config.presence_penalty,
        top_p=config.top_p,
        max_tokens=config.max_tokens,
        n=config.n,
        temperature=config.temperature,
    )

    if azure:
        if config.api_base is None:
            msg = "Azure OpenAI Chat LLM requires an API base"
            raise ValueError(msg)

        audience = config.audience or defs.AZURE_AUDIENCE
        return AzureOpenAIConfig(
            api_key=config.api_key,
            endpoint=config.api_base,
            json_strategy=json_strategy,
            api_version=config.api_version,
            organization=config.organization,
            max_retries=config.max_retries,
            max_retry_wait=config.max_retry_wait,
            requests_per_minute=config.requests_per_minute,
            tokens_per_minute=config.tokens_per_minute,
            cognitive_services_endpoint=audience,
            timeout=config.request_timeout,
            max_concurrency=config.concurrent_requests,
            model=config.model,
            encoding=encoding_model,
            deployment=config.deployment_name,
            chat_parameters=chat_parameters,
        )
    return PublicOpenAIConfig(
        api_key=config.api_key,
        base_url=config.api_base,
        json_strategy=json_strategy,
        organization=config.organization,
        max_retries=config.max_retries,
        max_retry_wait=config.max_retry_wait,
        requests_per_minute=config.requests_per_minute,
        tokens_per_minute=config.tokens_per_minute,
        timeout=config.request_timeout,
        max_concurrency=config.concurrent_requests,
        model=config.model,
        encoding=encoding_model,
        chat_parameters=chat_parameters,
    )


def _load_azure_openai_chat_llm(
    on_error: ErrorHandlerFn, cache: LLMCache, config: LanguageModelConfig
):
    return _load_openai_chat_llm(on_error, cache, config, True)


def _load_azure_openai_embeddings_llm(
    on_error: ErrorHandlerFn, cache: LLMCache, config: LanguageModelConfig
):
    return _load_openai_embeddings_llm(on_error, cache, config, True)


def _load_static_response(
    _on_error: ErrorHandlerFn, _cache: PipelineCache, config: LanguageModelConfig
) -> ChatLLM:
    if config.responses is None:
        msg = "Static response LLM requires responses"
        raise ValueError(msg)
    return MockChatLLM(config.responses or [])


loaders = {
    LLMType.OpenAIChat: {
        "load": _load_openai_chat_llm,
        "chat": True,
    },
    LLMType.AzureOpenAIChat: {
        "load": _load_azure_openai_chat_llm,
        "chat": True,
    },
    LLMType.OpenAIEmbedding: {
        "load": _load_openai_embeddings_llm,
        "chat": False,
    },
    LLMType.AzureOpenAIEmbedding: {
        "load": _load_azure_openai_embeddings_llm,
        "chat": False,
    },
    LLMType.StaticResponse: {
        "load": _load_static_response,
        "chat": False,
    },
}


def _create_openai_chat_llm(
    configuration: OpenAIConfig,
    on_error: ErrorHandlerFn,
    cache: LLMCache,
) -> ChatLLM:
    """Create an openAI chat llm."""
    client = create_openai_client(configuration)
    return create_openai_chat_llm(
        configuration,
        client=client,
        cache=cache,
        events=GraphRagLLMEvents(on_error),
    )


def _create_openai_embeddings_llm(
    configuration: OpenAIConfig,
    on_error: ErrorHandlerFn,
    cache: LLMCache,
) -> EmbeddingsLLM:
    """Create an openAI embeddings llm."""
    client = create_openai_client(configuration)
    return create_openai_embeddings_llm(
        configuration,
        client=client,
        cache=cache,
        events=GraphRagLLMEvents(on_error),
    )
