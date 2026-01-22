# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""MockLLMEmbedding."""

from typing import TYPE_CHECKING, Any, Unpack

import litellm

from graphrag_llm.embedding.embedding import LLMEmbedding
from graphrag_llm.utils import create_embedding_response

if TYPE_CHECKING:
    from graphrag_llm.config import ModelConfig
    from graphrag_llm.metrics import MetricsStore
    from graphrag_llm.tokenizer import Tokenizer
    from graphrag_llm.types import (
        LLMEmbeddingArgs,
        LLMEmbeddingResponse,
    )

litellm.suppress_debug_info = True


class MockLLMEmbedding(LLMEmbedding):
    """MockLLMEmbedding."""

    _metrics_store: "MetricsStore"
    _tokenizer: "Tokenizer"
    _mock_responses: list[float]
    _mock_index: int = 0

    def __init__(
        self,
        *,
        model_config: "ModelConfig",
        tokenizer: "Tokenizer",
        metrics_store: "MetricsStore",
        **kwargs: Any,
    ):
        """Initialize MockLLMEmbedding."""
        self._tokenizer = tokenizer
        self._metrics_store = metrics_store

        mock_responses = model_config.mock_responses
        if not isinstance(mock_responses, list) or len(mock_responses) == 0:
            msg = "ModelConfig.mock_responses must be a non-empty list of embedding responses."
            raise ValueError(msg)

        if not all(isinstance(resp, float) for resp in mock_responses):
            msg = "Each item in ModelConfig.mock_responses must be a float."
            raise ValueError(msg)

        self._mock_responses = mock_responses  # type: ignore

    def embedding(
        self, /, **kwargs: Unpack["LLMEmbeddingArgs"]
    ) -> "LLMEmbeddingResponse":
        """Sync embedding method."""
        input = kwargs.get("input")
        response = create_embedding_response(
            self._mock_responses, batch_size=len(input)
        )
        self._mock_index += 1
        return response

    async def embedding_async(
        self, /, **kwargs: Unpack["LLMEmbeddingArgs"]
    ) -> "LLMEmbeddingResponse":
        """Async embedding method."""
        return self.embedding(**kwargs)

    @property
    def metrics_store(self) -> "MetricsStore":
        """Get metrics store."""
        return self._metrics_store

    @property
    def tokenizer(self) -> "Tokenizer":
        """Get tokenizer."""
        return self._tokenizer
