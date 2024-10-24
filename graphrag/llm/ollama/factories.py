# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Factory functions for creating OpenAI LLMs."""

import asyncio

from graphrag.llm.base import CachingLLM, RateLimitingLLM
from graphrag.llm.limiting import LLMLimiter
from graphrag.llm.types import (
    LLM,
    CompletionLLM,
    EmbeddingLLM,
    ErrorHandlerFn,
    LLMCache,
    LLMInvocationFn,
    OnCacheActionFn,
)
from graphrag.llm.utils import (
    RATE_LIMIT_ERRORS,
    RETRYABLE_ERRORS,
    get_sleep_time_from_error,
    get_token_counter,
)
from graphrag.llm.openai.openai_history_tracking_llm import OpenAIHistoryTrackingLLM
from graphrag.llm.openai.openai_token_replacing_llm import OpenAITokenReplacingLLM

from .json_parsing_llm import JsonParsingLLM
from .ollama_chat_llm import OllamaChatLLM
from .ollama_completion_llm import OllamaCompletionLLM
from .ollama_configuration import OllamaConfiguration
from .ollama_embeddings_llm import OllamaEmbeddingsLLM
from .types import OllamaClientType


def create_ollama_chat_llm(
    client: OllamaClientType,
    config: OllamaConfiguration,
    cache: LLMCache | None = None,
    limiter: LLMLimiter | None = None,
    semaphore: asyncio.Semaphore | None = None,
    on_invoke: LLMInvocationFn | None = None,
    on_error: ErrorHandlerFn | None = None,
    on_cache_hit: OnCacheActionFn | None = None,
    on_cache_miss: OnCacheActionFn | None = None,
) -> CompletionLLM:
    """Create an OpenAI chat LLM."""
    operation = "chat"
    result = OllamaChatLLM(client, config)
    result.on_error(on_error)
    if limiter is not None or semaphore is not None:
        result = _rate_limited(result, config, operation, limiter, semaphore, on_invoke)
    if cache is not None:
        result = _cached(result, config, operation, cache, on_cache_hit, on_cache_miss)
    result = OpenAIHistoryTrackingLLM(result)
    result = OpenAITokenReplacingLLM(result)
    return JsonParsingLLM(result)


def create_ollama_completion_llm(
    client: OllamaClientType,
    config: OllamaConfiguration,
    cache: LLMCache | None = None,
    limiter: LLMLimiter | None = None,
    semaphore: asyncio.Semaphore | None = None,
    on_invoke: LLMInvocationFn | None = None,
    on_error: ErrorHandlerFn | None = None,
    on_cache_hit: OnCacheActionFn | None = None,
    on_cache_miss: OnCacheActionFn | None = None,
) -> CompletionLLM:
    """Create an OpenAI completion LLM."""
    operation = "completion"
    result = OllamaCompletionLLM(client, config)
    result.on_error(on_error)
    if limiter is not None or semaphore is not None:
        result = _rate_limited(result, config, operation, limiter, semaphore, on_invoke)
    if cache is not None:
        result = _cached(result, config, operation, cache, on_cache_hit, on_cache_miss)
    return OpenAITokenReplacingLLM(result)


def create_ollama_embedding_llm(
    client: OllamaClientType,
    config: OllamaConfiguration,
    cache: LLMCache | None = None,
    limiter: LLMLimiter | None = None,
    semaphore: asyncio.Semaphore | None = None,
    on_invoke: LLMInvocationFn | None = None,
    on_error: ErrorHandlerFn | None = None,
    on_cache_hit: OnCacheActionFn | None = None,
    on_cache_miss: OnCacheActionFn | None = None,
) -> EmbeddingLLM:
    """Create an OpenAI embeddings LLM."""
    operation = "embedding"
    result = OllamaEmbeddingsLLM(client, config)
    result.on_error(on_error)
    if limiter is not None or semaphore is not None:
        result = _rate_limited(result, config, operation, limiter, semaphore, on_invoke)
    if cache is not None:
        result = _cached(result, config, operation, cache, on_cache_hit, on_cache_miss)
    return result


def _rate_limited(
    delegate: LLM,
    config: OllamaConfiguration,
    operation: str,
    limiter: LLMLimiter | None,
    semaphore: asyncio.Semaphore | None,
    on_invoke: LLMInvocationFn | None,
):
    result = RateLimitingLLM(
        delegate,
        config,
        operation,
        RETRYABLE_ERRORS,
        RATE_LIMIT_ERRORS,
        limiter,
        semaphore,
        get_token_counter(config),
        get_sleep_time_from_error,
    )
    result.on_invoke(on_invoke)
    return result


def _cached(
    delegate: LLM,
    config: OllamaConfiguration,
    operation: str,
    cache: LLMCache,
    on_cache_hit: OnCacheActionFn | None,
    on_cache_miss: OnCacheActionFn | None,
):
    cache_args = config.get_completion_cache_args()
    result = CachingLLM(delegate, cache_args, operation, cache)
    result.on_cache_hit(on_cache_hit)
    result.on_cache_miss(on_cache_miss)
    return result
