# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Completion factory."""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from graphrag_common.factory import Factory

from graphrag_llm.cache import create_cache_key
from graphrag_llm.config.tokenizer_config import TokenizerConfig
from graphrag_llm.config.types import LLMProviderType
from graphrag_llm.metrics.noop_metrics_store import NoopMetricsStore
from graphrag_llm.tokenizer.tokenizer_factory import create_tokenizer

if TYPE_CHECKING:
    from graphrag_cache import Cache, CacheKeyCreator
    from graphrag_common.factory import ServiceScope

    from graphrag_llm.completion.completion import LLMCompletion
    from graphrag_llm.config import ModelConfig
    from graphrag_llm.metrics import MetricsProcessor, MetricsStore
    from graphrag_llm.rate_limit import RateLimiter
    from graphrag_llm.retry import Retry
    from graphrag_llm.tokenizer import Tokenizer


class CompletionFactory(Factory["LLMCompletion"]):
    """Factory for creating Completion instances."""


completion_factory = CompletionFactory()


def register_completion(
    completion_type: str,
    completion_initializer: Callable[..., "LLMCompletion"],
    scope: "ServiceScope" = "transient",
) -> None:
    """Register a custom completion implementation.

    Args
    ----
        completion_type: str
            The completion id to register.
        completion_initializer: Callable[..., LLMCompletion]
            The completion initializer to register.
        scope: ServiceScope (default: "transient")
            The service scope for the completion.
    """
    completion_factory.register(completion_type, completion_initializer, scope)


def create_completion(
    model_config: "ModelConfig",
    *,
    cache: "Cache | None" = None,
    cache_key_creator: "CacheKeyCreator | None" = None,
    tokenizer: "Tokenizer | None" = None,
) -> "LLMCompletion":
    """Create a Completion instance based on the model configuration.

    Args
    ----
        model_config: ModelConfig
            The configuration for the model.
        cache: Cache | None (default: None)
            An optional cache instance.
        cache_key_creator: CacheKeyCreator | None (default: create_cache_key)
            An optional cache key creator function.
            (dict[str, Any]) -> str
        tokenizer: Tokenizer | None (default: litellm)
            An optional tokenizer instance.

    Returns
    -------
        LLMCompletion:
            An instance of a LLMCompletion subclass.
    """
    cache_key_creator = cache_key_creator or create_cache_key
    model_id = f"{model_config.model_provider}/{model_config.model}"
    strategy = model_config.type
    extra: dict[str, Any] = model_config.model_extra or {}

    if strategy not in completion_factory:
        match strategy:
            case LLMProviderType.LiteLLM:
                from graphrag_llm.completion.lite_llm_completion import (
                    LiteLLMCompletion,
                )

                register_completion(
                    completion_type=LLMProviderType.LiteLLM,
                    completion_initializer=LiteLLMCompletion,
                    scope="singleton",
                )
            case LLMProviderType.MockLLM:
                from graphrag_llm.completion.mock_llm_completion import (
                    MockLLMCompletion,
                )

                register_completion(
                    completion_type=LLMProviderType.MockLLM,
                    completion_initializer=MockLLMCompletion,
                )
            case _:
                msg = f"ModelConfig.type '{strategy}' is not registered in the CompletionFactory. Registered strategies: {', '.join(completion_factory.keys())}"
                raise ValueError(msg)

    tokenizer = tokenizer or create_tokenizer(TokenizerConfig(model_id=model_id))

    rate_limiter: RateLimiter | None = None
    if model_config.rate_limit:
        from graphrag_llm.rate_limit.rate_limit_factory import create_rate_limiter

        rate_limiter = create_rate_limiter(rate_limit_config=model_config.rate_limit)

    retrier: Retry | None = None
    if model_config.retry:
        from graphrag_llm.retry.retry_factory import create_retry

        retrier = create_retry(retry_config=model_config.retry)

    metrics_store: MetricsStore = NoopMetricsStore()
    metrics_processor: MetricsProcessor | None = None
    if model_config.metrics:
        from graphrag_llm.metrics import create_metrics_processor, create_metrics_store

        metrics_store = create_metrics_store(
            config=model_config.metrics,
            id=model_id,
        )
        metrics_processor = create_metrics_processor(model_config.metrics)

    return completion_factory.create(
        strategy=strategy,
        init_args={
            **extra,
            "model_id": model_id,
            "model_config": model_config,
            "tokenizer": tokenizer,
            "metrics_store": metrics_store,
            "metrics_processor": metrics_processor,
            "rate_limiter": rate_limiter,
            "retrier": retrier,
            "cache": cache,
            "cache_key_creator": cache_key_creator,
        },
    )
