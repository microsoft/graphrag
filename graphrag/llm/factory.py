# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing a factory for supported llm types."""

from collections.abc import Callable
from typing import Any, ClassVar

from graphrag.config.enums import LLMType
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

    _chat_registry: ClassVar[dict[str, Callable[..., ChatLLM]]] = {}
    _embedding_registry: ClassVar[dict[str, Callable[..., EmbeddingLLM]]] = {}

    @classmethod
    def register_chat(cls, model_type: str, creator: Callable[..., ChatLLM]) -> None:
        """Register a ChatLLM implementation."""
        cls._chat_registry[model_type] = creator

    @classmethod
    def register_embedding(
        cls, model_type: str, creator: Callable[..., EmbeddingLLM]
    ) -> None:
        """Register an EmbeddingLLM implementation."""
        cls._embedding_registry[model_type] = creator

    @classmethod
    def create_chat_llm(cls, model_type: str, **kwargs: Any) -> ChatLLM:
        """
        Create a ChatLLM instance.

        Args:
            model_type: The type of ChatLLM to create.
            **kwargs: Additional keyword arguments for the ChatLLM constructor.

        Returns
        -------
            A ChatLLM instance.
        """
        if model_type not in cls._chat_registry:
            msg = f"ChatLLM implementation '{model_type}' is not registered."
            raise ValueError(msg)
        return cls._chat_registry[model_type](**kwargs)

    @classmethod
    def create_embedding_llm(cls, model_type: str, **kwargs: Any) -> EmbeddingLLM:
        """
        Create an EmbeddingLLM instance.

        Args:
            model_type: The type of EmbeddingLLM to create.
            **kwargs: Additional keyword arguments for the EmbeddingLLM constructor.

        Returns
        -------
            An EmbeddingLLM instance.
        """
        if model_type not in cls._embedding_registry:
            msg = f"EmbeddingLLM implementation '{model_type}' is not registered."
            raise ValueError(msg)
        return cls._embedding_registry[model_type](**kwargs)


# --- Register default implementations ---
LLMFactory.register_chat(
    LLMType.AzureOpenAIChat, lambda **kwargs: AzureOpenAIChatFNLLM(**kwargs)
)
LLMFactory.register_chat(LLMType.OpenAIChat, lambda **kwargs: OpenAIChatFNLLM(**kwargs))
LLMFactory.register_chat(LLMType.MockChat, lambda **kwargs: MockChatLLM(**kwargs))

LLMFactory.register_embedding(
    LLMType.AzureOpenAIEmbedding, lambda **kwargs: AzureOpenAIEmbeddingFNLLM(**kwargs)
)
LLMFactory.register_embedding(
    LLMType.OpenAIEmbedding, lambda **kwargs: OpenAIEmbeddingFNLLM(**kwargs)
)
LLMFactory.register_embedding(
    LLMType.MockEmbedding, lambda **kwargs: MockEmbeddingLLM(**kwargs)
)
