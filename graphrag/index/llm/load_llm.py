# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Load llm utilities."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from fnllm import LLMEvents
from fnllm.openai import (
    OpenAIConfig,
    OpenAIEmbeddingsLLMInstance,
    OpenAITextChatLLMInstance,
    create_openai_chat_llm,
    create_openai_client,
    create_openai_embeddings_llm,
)
from pydantic import TypeAdapter

from graphrag.config.enums import LLMType

from .mock_llm import MockChatLLM

if TYPE_CHECKING:
    from datashaper import VerbCallbacks
    from fnllm.caching import Cache as LLMCache

    from graphrag.config.models.llm_parameters import LLMParameters
    from graphrag.index.cache import PipelineCache
    from graphrag.index.typing import ErrorHandlerFn

log = logging.getLogger(__name__)


validator = TypeAdapter(OpenAIConfig)


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


def load_llm(
    name: str,
    config: LLMParameters,
    *,
    callbacks: VerbCallbacks,
    cache: PipelineCache | None,
    chat_only=False,
) -> OpenAITextChatLLMInstance:
    """Load the LLM for the entity extraction chain."""
    on_error = _create_error_handler(callbacks)
    llm_type = config.type

    if llm_type in loaders:
        if chat_only and not loaders[llm_type]["chat"]:
            msg = f"LLM type {llm_type} does not support chat"
            raise ValueError(msg)
        if cache is not None:
            cache = cache.child(name)

        loader = loaders[llm_type]
        return loader["load"](on_error, cache, config or {})

    msg = f"Unknown LLM type {llm_type}"
    raise ValueError(msg)


def load_llm_embeddings(
    name: str,
    llm_config: LLMParameters,
    *,
    callbacks: VerbCallbacks,
    cache: PipelineCache | None,
    chat_only=False,
) -> OpenAIEmbeddingsLLMInstance:
    """Load the LLM for the entity extraction chain."""
    on_error = _create_error_handler(callbacks)
    llm_type = llm_config.type
    if llm_type in loaders:
        if chat_only and not loaders[llm_type]["chat"]:
            msg = f"LLM type {llm_type} does not support chat"
            raise ValueError(msg)
        if cache is not None:
            cache = cache.child(name)
        return loaders[llm_type]["load"](on_error, cache, llm_config or {})

    msg = f"Unknown LLM type {llm_type}"
    raise ValueError(msg)


def _create_error_handler(callbacks: VerbCallbacks) -> ErrorHandlerFn:
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
    config: dict[str, Any],
    azure=False,
):
    configuration = validator.validate_python({
        **_get_base_config(config),
        "azure": azure,
        "model": config.get("model", "gpt-4-turbo-preview"),
        "deployment": config.get("deployment_name"),
        "chat_parameters": {
            "frequency_penalty": config.get("frequency_penalty", 0),
            "presence_penalty": config.get("presence_penalty", 0),
            "top_p": config.get("top_p", 1),
            "max_tokens": config.get("max_tokens", 4000),
            "n": config.get("n"),
            "temperature": config.get("temperature", 0.0),
        },
    })
    return _create_openai_chat_llm(
        configuration,
        on_error,
        cache,
    )


def _load_openai_embeddings_llm(
    on_error: ErrorHandlerFn,
    cache: LLMCache,
    config: dict[str, Any],
    azure=False,
):
    configuration = validator.validate_python({
        **_get_base_config(config),
        "azure": azure,
        "model": config.get(
            "embeddings_model", config.get("model", "text-embedding-3-small")
        ),
        "deployment": config.get("deployment_name"),
    })
    return _create_openai_embeddings_llm(
        configuration,
        on_error,
        cache,
    )


def _load_azure_openai_chat_llm(
    on_error: ErrorHandlerFn, cache: LLMCache, config: dict[str, Any]
):
    return _load_openai_chat_llm(on_error, cache, config, True)


def _load_azure_openai_embeddings_llm(
    on_error: ErrorHandlerFn, cache: LLMCache, config: dict[str, Any]
):
    return _load_openai_embeddings_llm(on_error, cache, config, True)


def _get_base_config(config: dict[str, Any]) -> dict[str, Any]:
    api_key = config.get("api_key")

    return {
        # Pass in all parameterized values
        **config,
        # Set default values
        "api_key": api_key,
        "api_base": config.get("api_base"),
        "api_version": config.get("api_version"),
        "organization": config.get("organization"),
        "proxy": config.get("proxy"),
        "max_retries": config.get("max_retries", 10),
        "request_timeout": config.get("request_timeout", 60.0),
        "model_supports_json": config.get("model_supports_json"),
        "concurrent_requests": config.get("concurrent_requests", 4),
        "encoding_model": config.get("encoding_model", "cl100k_base"),
        "cognitive_services_endpoint": config.get("cognitive_services_endpoint"),
    }


def _load_static_response(
    _on_error: ErrorHandlerFn, _cache: PipelineCache, config: dict[str, Any]
) -> OpenAITextChatLLMInstance:
    return MockChatLLM(config.get("responses", []))


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
) -> OpenAITextChatLLMInstance:
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
) -> OpenAIEmbeddingsLLMInstance:
    """Create an openAI embeddings llm."""
    client = create_openai_client(configuration)
    return create_openai_embeddings_llm(
        configuration,
        client=client,
        cache=cache,
        events=GraphRagLLMEvents(on_error),
    )
