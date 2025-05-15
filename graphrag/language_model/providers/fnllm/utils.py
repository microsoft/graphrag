# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing utils for fnllm."""

from __future__ import annotations

import asyncio
import threading
from typing import TYPE_CHECKING, Any, TypeVar

from fnllm.base.config import JsonStrategy, RetryStrategy
from fnllm.openai import AzureOpenAIConfig, OpenAIConfig, PublicOpenAIConfig
from fnllm.openai.types.chat.parameters import OpenAIChatParameters

import graphrag.config.defaults as defs
from graphrag.language_model.providers.fnllm.cache import FNLLMCacheProvider

if TYPE_CHECKING:
    from collections.abc import Coroutine

    from graphrag.cache.pipeline_cache import PipelineCache
    from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
    from graphrag.config.models.language_model_config import (
        LanguageModelConfig,
    )
    from graphrag.index.typing.error_handler import ErrorHandlerFn


def _create_cache(cache: PipelineCache | None, name: str) -> FNLLMCacheProvider | None:
    """Create an FNLLM cache from a pipeline cache."""
    if cache is None:
        return None
    return FNLLMCacheProvider(cache).child(name)


def _create_error_handler(callbacks: WorkflowCallbacks) -> ErrorHandlerFn:
    """Create an error handler from a WorkflowCallbacks."""

    def on_error(
        error: BaseException | None = None,
        stack: str | None = None,
        details: dict | None = None,
    ) -> None:
        callbacks.error("Error Invoking LLM", error, stack, details)

    return on_error


def _create_openai_config(config: LanguageModelConfig, azure: bool) -> OpenAIConfig:
    """Create an OpenAIConfig from a LanguageModelConfig."""
    encoding_model = config.encoding_model
    json_strategy = (
        JsonStrategy.VALID if config.model_supports_json else JsonStrategy.LOOSE
    )
    chat_parameters = OpenAIChatParameters(
        **get_openai_model_parameters_from_config(config)
    )

    if azure:
        if config.api_base is None:
            msg = "Azure OpenAI Chat LLM requires an API base"
            raise ValueError(msg)

        audience = config.audience or defs.COGNITIVE_SERVICES_AUDIENCE
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
            audience=audience,
            retry_strategy=RetryStrategy(config.retry_strategy),
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
        retry_strategy=RetryStrategy(config.retry_strategy),
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


# FNLLM does not support sync operations, so we workaround running in an available loop/thread.
T = TypeVar("T")

_loop = asyncio.new_event_loop()

_thr = threading.Thread(target=_loop.run_forever, name="Async Runner", daemon=True)


def run_coroutine_sync(coroutine: Coroutine[Any, Any, T]) -> T:
    """
    Run a coroutine synchronously.

    Args:
        coroutine: The coroutine to run.

    Returns
    -------
        The result of the coroutine.
    """
    if not _thr.is_alive():
        _thr.start()
    future = asyncio.run_coroutine_threadsafe(coroutine, _loop)
    return future.result()


def is_reasoning_model(model: str) -> bool:
    """Return whether the model uses a known OpenAI reasoning model."""
    return model.lower() in {"o1", "o1-mini", "o3-mini"}


def get_openai_model_parameters_from_config(
    config: LanguageModelConfig,
) -> dict[str, Any]:
    """Get the model parameters for a given config, adjusting for reasoning API differences."""
    return get_openai_model_parameters_from_dict(config.model_dump())


def get_openai_model_parameters_from_dict(config: dict[str, Any]) -> dict[str, Any]:
    """Get the model parameters for a given config, adjusting for reasoning API differences."""
    params = {
        "n": config.get("n"),
    }
    if is_reasoning_model(config["model"]):
        params["max_completion_tokens"] = config.get("max_completion_tokens")
        params["reasoning_effort"] = config.get("reasoning_effort")
    else:
        params["max_tokens"] = config.get("max_tokens")
        params["temperature"] = config.get("temperature")
        params["frequency_penalty"] = config.get("frequency_penalty")
        params["presence_penalty"] = config.get("presence_penalty")
        params["top_p"] = config.get("top_p")

    if config.get("response_format"):
        params["response_format"] = config["response_format"]

    return params
