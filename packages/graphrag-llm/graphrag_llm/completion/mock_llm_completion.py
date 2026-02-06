# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Mock LLMCompletion."""

from typing import TYPE_CHECKING, Any, Unpack

import litellm

from graphrag_llm.completion.completion import LLMCompletion
from graphrag_llm.utils import (
    create_completion_response,
    structure_completion_response,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from graphrag_llm.config import ModelConfig
    from graphrag_llm.metrics import MetricsStore
    from graphrag_llm.tokenizer import Tokenizer
    from graphrag_llm.types import (
        LLMCompletionArgs,
        LLMCompletionChunk,
        LLMCompletionResponse,
        ResponseFormat,
    )


litellm.suppress_debug_info = True


class MockLLMCompletion(LLMCompletion):
    """LLMCompletion based on litellm."""

    _metrics_store: "MetricsStore"
    _tokenizer: "Tokenizer"
    _mock_responses: list[str]
    _mock_index: int = 0

    def __init__(
        self,
        *,
        model_config: "ModelConfig",
        tokenizer: "Tokenizer",
        metrics_store: "MetricsStore",
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
        self._tokenizer = tokenizer
        self._metrics_store = metrics_store

        mock_responses = model_config.mock_responses
        if not isinstance(mock_responses, list) or len(mock_responses) == 0:
            msg = "ModelConfig.mock_responses must be a non-empty list."
            raise ValueError(msg)

        if not all(isinstance(resp, str) for resp in mock_responses):
            msg = "Each item in ModelConfig.mock_responses must be a string."
            raise ValueError(msg)

        self._mock_responses = mock_responses  # type: ignore

    def completion(
        self,
        /,
        **kwargs: Unpack["LLMCompletionArgs[ResponseFormat]"],
    ) -> "LLMCompletionResponse[ResponseFormat] | Iterator[LLMCompletionChunk]":
        """Sync completion method."""
        response_format = kwargs.pop("response_format", None)

        is_streaming = kwargs.get("stream", False)
        if is_streaming:
            msg = "MockLLMCompletion does not support streaming completions."
            raise ValueError(msg)

        response = create_completion_response(
            self._mock_responses[self._mock_index % len(self._mock_responses)]
        )
        self._mock_index += 1
        if response_format is not None:
            structured_response = structure_completion_response(
                response.content, response_format
            )
            response.formatted_response = structured_response
        return response

    async def completion_async(
        self,
        /,
        **kwargs: Unpack["LLMCompletionArgs[ResponseFormat]"],
    ) -> "LLMCompletionResponse[ResponseFormat] | AsyncIterator[LLMCompletionChunk]":
        """Async completion method."""
        return self.completion(**kwargs)  # type: ignore

    @property
    def metrics_store(self) -> "MetricsStore":
        """Get metrics store."""
        return self._metrics_store

    @property
    def tokenizer(self) -> "Tokenizer":
        """Get tokenizer."""
        return self._tokenizer
