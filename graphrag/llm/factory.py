# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing a factory for supported llm types."""

from typing import Any, Callable

from config.enums import LLMType

from graphrag.llm.protocol import ChatLLM, EmbeddingLLM
from graphrag.llm.providers.fnllm.models import (
    AzureOpenAIChatFNLLM,
    AzureOpenAIEmbeddingFNLLM,
    OpenAIChatFNLLM,
    OpenAIEmbeddingFNLLM,
)
from graphrag.llm.providers.mock_provider import MockChatLLM, MockEmbeddingLLM


class LLMFactory:
    """A factory for creating LLM instances."""

    _chat_registry: dict[str, Callable[..., ChatLLM]] = {}
    _embedding_registry: dict[str, Callable[..., EmbeddingLLM]] = {}

    @classmethod
    def register_chat(cls, key: str, creator: Callable[..., ChatLLM]) -> None:
        cls._chat_registry[key] = creator

    @classmethod
    def register_embedding(cls, key: str, creator: Callable[..., EmbeddingLLM]) -> None:
        cls._embedding_registry[key] = creator

    @classmethod
    def create_chat_llm(cls, key: str, **kwargs: Any) -> ChatLLM:
        if key not in cls._chat_registry:
            msg = f"ChatLLM implementation '{key}' is not registered."
            raise ValueError(msg)
        return cls._chat_registry[key](**kwargs)

    @classmethod
    def create_embedding_llm(cls, key: str, **kwargs: Any) -> EmbeddingLLM:
        if key not in cls._embedding_registry:
            msg = f"EmbeddingLLM implementation '{key}' is not registered."
            raise ValueError(msg)
        return cls._embedding_registry[key](**kwargs)


# --- Register default implementations ---
LLMFactory.register_chat(
    LLMType.AzureOpenAIChat, lambda **kwargs: AzureOpenAIChatFNLLM(**kwargs)
)
LLMFactory.register_chat(LLMType.OpenAIChat, lambda **kwargs: OpenAIChatFNLLM(**kwargs))
LLMFactory.register_chat(LLMType.Mock, lambda **kwargs: MockChatLLM())

LLMFactory.register_embedding(
    LLMType.AzureOpenAIEmbedding, lambda **kwargs: AzureOpenAIEmbeddingFNLLM(**kwargs)
)
LLMFactory.register_embedding(
    LLMType.OpenAIEmbedding, lambda **kwargs: OpenAIEmbeddingFNLLM(**kwargs)
)
LLMFactory.register_embedding(LLMType.Mock, lambda **kwargs: MockEmbeddingLLM())
