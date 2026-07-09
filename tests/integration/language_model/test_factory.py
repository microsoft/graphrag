# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""LLMFactory Tests.

These tests will test the LLMFactory class and the creation of custom and provided LLMs.
"""

from typing import TYPE_CHECKING, Any, Unpack

from graphrag_llm.completion import (
    LLMCompletion,
    create_completion,
    register_completion,
)
from graphrag_llm.config import ModelConfig
from graphrag_llm.embedding import LLMEmbedding, create_embedding, register_embedding
from graphrag_llm.model_cost_registry import model_cost_registry

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from graphrag_llm.metrics import MetricsStore
    from graphrag_llm.tokenizer import Tokenizer
    from graphrag_llm.types import (
        LLMCompletionArgs,
        LLMCompletionChunk,
        LLMCompletionResponse,
        LLMEmbeddingArgs,
        LLMEmbeddingResponse,
        ResponseFormat,
    )


def test_create_custom_chat_model():
    class CustomChatModel(LLMCompletion):
        config: Any

        def __init__(self, **kwargs):
            pass

        def completion(
            self,
            /,
            **kwargs: Unpack["LLMCompletionArgs[ResponseFormat]"],
        ) -> "LLMCompletionResponse[ResponseFormat] | Iterator[LLMCompletionChunk]": ...

        async def completion_async(
            self,
            /,
            **kwargs: Unpack["LLMCompletionArgs[ResponseFormat]"],
        ) -> (
            "LLMCompletionResponse[ResponseFormat] | AsyncIterator[LLMCompletionChunk]"
        ): ...

        @property
        def metrics_store(self) -> "MetricsStore": ...

        @property
        def tokenizer(self) -> "Tokenizer": ...

    register_completion("custom_chat", CustomChatModel)

    model = create_completion(
        ModelConfig(
            type="custom_chat",
            model_provider="custom_provider",
            model="custom_chat_model",
        )
    )
    assert isinstance(model, CustomChatModel)


def test_minimax_m3_model_costs_registered():
    costs = model_cost_registry.get_model_costs("minimax/MiniMax-M3")

    assert costs is not None
    assert costs["input_cost_per_token"] == 0.6 / 1_000_000
    assert costs["output_cost_per_token"] == 2.4 / 1_000_000
    assert costs["cache_read_input_token_cost"] == 0.12 / 1_000_000
    assert costs["max_input_tokens"] == 1_000_000
    assert costs["mode"] == "chat"


def test_create_custom_embedding_llm():
    class CustomEmbeddingModel(LLMEmbedding):
        def __init__(self, **kwargs): ...

        def embedding(
            self, /, **kwargs: Unpack["LLMEmbeddingArgs"]
        ) -> "LLMEmbeddingResponse": ...

        async def embedding_async(
            self, /, **kwargs: Unpack["LLMEmbeddingArgs"]
        ) -> "LLMEmbeddingResponse": ...

        @property
        def metrics_store(self) -> "MetricsStore": ...

        @property
        def tokenizer(self) -> "Tokenizer": ...

    register_embedding("custom_embedding", CustomEmbeddingModel)

    model = create_embedding(
        ModelConfig(
            type="custom_embedding",
            model_provider="custom_provider",
            model="custom_embedding_model",
        )
    )

    assert isinstance(model, CustomEmbeddingModel)
