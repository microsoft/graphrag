# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""LLMCompletion based on litellm."""

from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING, Any, Unpack

import litellm
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from litellm import ModelResponse  # type: ignore

from graphrag_llm.completion.completion import LLMCompletion
from graphrag_llm.config.types import AuthMethod
from graphrag_llm.middleware import (
    with_middleware_pipeline,
)
from graphrag_llm.types import LLMCompletionChunk, LLMCompletionResponse
from graphrag_llm.utils import (
    structure_completion_response,
)

if TYPE_CHECKING:
    from graphrag_cache import Cache, CacheKeyCreator

    from graphrag_llm.config import ModelConfig
    from graphrag_llm.metrics import MetricsProcessor, MetricsStore
    from graphrag_llm.rate_limit import RateLimiter
    from graphrag_llm.retry import Retry
    from graphrag_llm.tokenizer import Tokenizer
    from graphrag_llm.types import (
        AsyncLLMCompletionFunction,
        LLMCompletionArgs,
        LLMCompletionFunction,
        LLMCompletionMessagesParam,
        Metrics,
        ResponseFormat,
    )


litellm.suppress_debug_info = True


class LiteLLMCompletion(LLMCompletion):
    """LLMCompletion based on litellm."""

    _model_config: "ModelConfig"
    _model_id: str
    _track_metrics: bool = False
    _metrics_store: "MetricsStore"
    _metrics_processor: "MetricsProcessor | None"
    _cache: "Cache | None"
    _cache_key_creator: "CacheKeyCreator"
    _tokenizer: "Tokenizer"
    _rate_limiter: "RateLimiter | None"
    _retrier: "Retry | None"

    def __init__(
        self,
        *,
        model_id: str,
        model_config: "ModelConfig",
        tokenizer: "Tokenizer",
        metrics_store: "MetricsStore",
        metrics_processor: "MetricsProcessor | None" = None,
        rate_limiter: "RateLimiter | None" = None,
        retrier: "Retry | None" = None,
        cache: "Cache | None" = None,
        cache_key_creator: "CacheKeyCreator",
        azure_cognitive_services_audience: str = "https://cognitiveservices.azure.com/.default",
        drop_unsupported_params: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialize LiteLLMCompletion.

        Args
        ----
            model_id: str
                The LiteLLM model ID, e.g., "openai/gpt-4o"
            model_config: ModelConfig
                The configuration for the model.
            tokenizer: Tokenizer
                The tokenizer to use.
            metrics_store: MetricsStore | None (default: None)
                The metrics store to use.
            metrics_processor: MetricsProcessor | None (default: None)
                The metrics processor to use.
            cache: Cache | None (default: None)
                An optional cache instance.
            cache_key_prefix: str | None (default: "chat")
                The cache key prefix. Required if cache is provided.
            rate_limiter: RateLimiter | None (default: None)
                The rate limiter to use.
            retrier: Retry | None (default: None)
                The retry strategy to use.
            azure_cognitive_services_audience: str (default: "https://cognitiveservices.azure.com/.default")
                The audience for Azure Cognitive Services when using Managed Identity.
            drop_unsupported_params: bool (default: True)
                Whether to drop unsupported parameters for the model provider.
        """
        self._model_id = model_id
        self._model_config = model_config
        self._tokenizer = tokenizer
        self._metrics_store = metrics_store
        self._metrics_processor = metrics_processor
        self._cache = cache
        self._track_metrics = metrics_processor is not None
        self._cache_key_creator = cache_key_creator
        self._rate_limiter = rate_limiter
        self._retrier = retrier

        self._completion, self._completion_async = _create_base_completions(
            model_config=model_config,
            drop_unsupported_params=drop_unsupported_params,
            azure_cognitive_services_audience=azure_cognitive_services_audience,
        )

        self._completion, self._completion_async = with_middleware_pipeline(
            model_config=self._model_config,
            model_fn=self._completion,
            async_model_fn=self._completion_async,
            request_type="chat",
            cache=self._cache,
            cache_key_creator=self._cache_key_creator,
            tokenizer=self._tokenizer,
            metrics_processor=self._metrics_processor,
            rate_limiter=self._rate_limiter,
            retrier=self._retrier,
        )

    def completion(
        self,
        /,
        **kwargs: Unpack["LLMCompletionArgs[ResponseFormat]"],
    ) -> "LLMCompletionResponse[ResponseFormat] | Iterator[LLMCompletionChunk]":
        """Sync completion method."""
        messages: LLMCompletionMessagesParam = kwargs.pop("messages")
        response_format = kwargs.pop("response_format", None)

        is_streaming = kwargs.get("stream") or False

        if response_format is not None and is_streaming:
            msg = "response_format is not supported for streaming completions."
            raise ValueError(msg)

        request_metrics: Metrics | None = kwargs.pop("metrics", None) or {}
        if not self._track_metrics:
            request_metrics = None

        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        try:
            response = self._completion(
                messages=messages,
                metrics=request_metrics,
                response_format=response_format,
                **kwargs,  # type: ignore
            )
            if response_format is not None:
                structured_response = structure_completion_response(
                    response.content, response_format
                )
                response.formatted_response = structured_response
            return response
        finally:
            if request_metrics is not None:
                self._metrics_store.update_metrics(metrics=request_metrics)

    async def completion_async(
        self,
        /,
        **kwargs: Unpack["LLMCompletionArgs[ResponseFormat]"],
    ) -> "LLMCompletionResponse[ResponseFormat] | AsyncIterator[LLMCompletionChunk]":
        """Async completion method."""
        messages: LLMCompletionMessagesParam = kwargs.pop("messages")
        response_format = kwargs.pop("response_format", None)

        is_streaming = kwargs.get("stream") or False

        if response_format is not None and is_streaming:
            msg = "response_format is not supported for streaming completions."
            raise ValueError(msg)

        request_metrics: Metrics | None = kwargs.pop("metrics", None) or {}
        if not self._track_metrics:
            request_metrics = None

        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        try:
            response = await self._completion_async(
                messages=messages,
                metrics=request_metrics,
                response_format=response_format,
                **kwargs,  # type: ignore
            )
            if response_format is not None:
                structured_response = structure_completion_response(
                    response.content, response_format
                )
                response.formatted_response = structured_response
            return response
        finally:
            if request_metrics is not None:
                self._metrics_store.update_metrics(metrics=request_metrics)

    @property
    def metrics_store(self) -> "MetricsStore":
        """Get metrics store."""
        return self._metrics_store

    @property
    def tokenizer(self) -> "Tokenizer":
        """Get tokenizer."""
        return self._tokenizer


def _create_base_completions(
    *,
    model_config: "ModelConfig",
    drop_unsupported_params: bool,
    azure_cognitive_services_audience: str,
) -> tuple["LLMCompletionFunction", "AsyncLLMCompletionFunction"]:
    """Create base completions for LiteLLM.

    Convert litellm completion functions to graphrag_llm LLMCompletionFunction.
    LLMCompletionFunction is close to the litellm completion function signature,
    but uses a few extra params such as metrics. Remove graphrag_llm LLMCompletionFunction
    specific params before calling litellm completion functions.
    """
    model_provider = model_config.model_provider
    model = model_config.azure_deployment_name or model_config.model

    base_args: dict[str, Any] = {
        "drop_params": drop_unsupported_params,
        "model": f"{model_provider}/{model}",
        "api_key": model_config.api_key,
        "api_base": model_config.api_base,
        "api_version": model_config.api_version,
        **model_config.call_args,
    }

    if model_config.auth_method == AuthMethod.AzureManagedIdentity:
        base_args["azure_ad_token_provider"] = get_bearer_token_provider(
            DefaultAzureCredential(), azure_cognitive_services_audience
        )

    def _base_completion(
        **kwargs: Any,
    ) -> LLMCompletionResponse | Iterator[LLMCompletionChunk]:
        kwargs.pop("metrics", None)
        mock_response: str | None = kwargs.pop("mock_response", None)
        json_object: bool | None = kwargs.pop("response_format_json_object", None)
        new_args: dict[str, Any] = {**base_args, **kwargs}

        if model_config.mock_responses and mock_response is not None:
            new_args["mock_response"] = mock_response

        if json_object and "response_format" not in new_args:
            new_args["response_format"] = {"type": "json_object"}

        response = litellm.completion(
            **new_args,
        )
        if isinstance(response, ModelResponse):
            return LLMCompletionResponse(**response.model_dump())

        def _run_iterator() -> Iterator[LLMCompletionChunk]:
            for chunk in response:
                yield LLMCompletionChunk(**chunk.model_dump())

        return _run_iterator()

    async def _base_completion_async(
        **kwargs: Any,
    ) -> LLMCompletionResponse | AsyncIterator[LLMCompletionChunk]:
        kwargs.pop("metrics", None)
        mock_response: str | None = kwargs.pop("mock_response", None)
        json_object: bool | None = kwargs.pop("response_format_json_object", None)
        new_args: dict[str, Any] = {**base_args, **kwargs}

        if model_config.mock_responses and mock_response is not None:
            new_args["mock_response"] = mock_response

        if json_object and "response_format" not in new_args:
            new_args["response_format"] = {"type": "json_object"}

        response = await litellm.acompletion(
            **new_args,
        )
        if isinstance(response, ModelResponse):
            return LLMCompletionResponse(**response.model_dump())

        async def _run_iterator() -> AsyncIterator[LLMCompletionChunk]:
            async for chunk in response:
                yield LLMCompletionChunk(**chunk.model_dump())  # type: ignore

        return _run_iterator()

    return (_base_completion, _base_completion_async)
