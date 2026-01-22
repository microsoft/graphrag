# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Wraps model functions in middleware pipeline."""

from typing import TYPE_CHECKING, Literal

from graphrag_llm.middleware.with_cache import with_cache
from graphrag_llm.middleware.with_errors_for_testing import with_errors_for_testing
from graphrag_llm.middleware.with_logging import with_logging
from graphrag_llm.middleware.with_metrics import with_metrics
from graphrag_llm.middleware.with_rate_limiting import with_rate_limiting
from graphrag_llm.middleware.with_request_count import with_request_count
from graphrag_llm.middleware.with_retries import with_retries

if TYPE_CHECKING:
    from graphrag_cache import Cache, CacheKeyCreator

    from graphrag_llm.config import ModelConfig
    from graphrag_llm.metrics import MetricsProcessor
    from graphrag_llm.rate_limit import RateLimiter
    from graphrag_llm.retry import Retry
    from graphrag_llm.tokenizer import Tokenizer
    from graphrag_llm.types import (
        AsyncLLMFunction,
        LLMFunction,
    )


def with_middleware_pipeline(
    *,
    model_config: "ModelConfig",
    model_fn: "LLMFunction",
    async_model_fn: "AsyncLLMFunction",
    metrics_processor: "MetricsProcessor | None",
    cache: "Cache | None",
    cache_key_creator: "CacheKeyCreator",
    request_type: Literal["chat", "embedding"],
    tokenizer: "Tokenizer",
    rate_limiter: "RateLimiter | None",
    retrier: "Retry | None",
) -> tuple[
    "LLMFunction",
    "AsyncLLMFunction",
]:
    """Wrap model functions in middleware pipeline.

    Full Pipeline Order:
        - with_requests_counts: Counts incoming requests and
            successes, and failures that bubble back up.
        - with_cache: Returns cached responses when available
            and caches new successful responses that bubble back up.
        - with_retries: Retries failed requests.
            Since the retry middleware occurs prior to rate limiting,
            all retries get back in line for rate limiting. This is
            to avoid threads that retry rapidly against an endpoint,
            thus increasing the required cooldown.
        - with_rate_limiting: Rate limits requests.
        - with_metrics: Collects metrics about the request and responses.
        - with_errors_for_testing: Raises errors for testing purposes.
            Relies on ModelConfig.failure_rate_for_testing to determine
            the failure rate. 'failure_rate_for_testing' is not an exposed
            configuration option and is only intended for internal testing.

    Args
    ----
        model_config: ModelConfig
            The model configuration.
        model_fn: LLMFunction
            The synchronous model function to wrap.
            Either a completion function or an embedding function.
        async_model_fn: AsyncLLMFunction
            The asynchronous model function to wrap.
            Either a completion function or an embedding function.
        metrics_processor: MetricsProcessor | None
            The metrics processor to use. If None, metrics middleware is skipped.
        cache: Cache | None
            The cache instance to use. If None, caching middleware is skipped.
        cache_key_creator: CacheKeyCreator
            The cache key creator to use.
        request_type: Literal["chat", "embedding"]
            The type of request, either "chat" or "embedding".
            The middleware pipeline is used for both completions and embeddings
            and some of the steps need to know which type of request it is.
        tokenizer: Tokenizer
            The tokenizer to use for rate limiting.
        rate_limiter: RateLimiter | None
            The rate limiter to use. If None, rate limiting middleware is skipped.
        retrier: Retry | None
            The retrier to use. If None, retry middleware is skipped.

    Returns
    -------
        tuple[LLMFunction, AsyncLLMFunction]
            The synchronous and asynchronous model functions wrapped in the middleware pipeline.
    """
    extra_config = model_config.model_extra or {}
    failure_rate_for_testing = extra_config.get("failure_rate_for_testing", 0.0)

    if failure_rate_for_testing > 0.0:
        model_fn, async_model_fn = with_errors_for_testing(
            sync_middleware=model_fn,
            async_middleware=async_model_fn,
            failure_rate=failure_rate_for_testing,
            exception_type=extra_config.get(
                "failure_rate_for_testing_exception_type", "ValueError"
            ),
            exception_args=extra_config.get("failure_rate_for_testing_exception_args"),
        )

    if metrics_processor:
        model_fn, async_model_fn = with_metrics(
            model_config=model_config,
            sync_middleware=model_fn,
            async_middleware=async_model_fn,
            metrics_processor=metrics_processor,
        )

    if rate_limiter:
        model_fn, async_model_fn = with_rate_limiting(
            sync_middleware=model_fn,
            async_middleware=async_model_fn,
            tokenizer=tokenizer,
            rate_limiter=rate_limiter,
        )

    if retrier:
        model_fn, async_model_fn = with_retries(
            sync_middleware=model_fn,
            async_middleware=async_model_fn,
            retrier=retrier,
        )

    if cache:
        model_fn, async_model_fn = with_cache(
            sync_middleware=model_fn,
            async_middleware=async_model_fn,
            request_type=request_type,
            cache=cache,
            cache_key_creator=cache_key_creator,
        )

    if metrics_processor:
        model_fn, async_model_fn = with_request_count(
            sync_middleware=model_fn,
            async_middleware=async_model_fn,
        )

    model_fn, async_model_fn = with_logging(
        sync_middleware=model_fn,
        async_middleware=async_model_fn,
    )

    return (model_fn, async_model_fn)
