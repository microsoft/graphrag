# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""A package containing a factory for supported llm types."""

from collections.abc import Callable
from typing import Any, ClassVar

from graphrag.config.enums import ModelType
from graphrag.language_model.protocol import ChatModel, EmbeddingModel
from graphrag.language_model.providers.fnllm.models import (
    AzureOpenAIChatFNLLM,
    AzureOpenAIEmbeddingFNLLM,
    OpenAIChatFNLLM,
    OpenAIEmbeddingFNLLM,
)


class ModelFactory:
    """A factory for creating Model instances."""

    _chat_registry: ClassVar[dict[str, Callable[..., ChatModel]]] = {}
    _embedding_registry: ClassVar[dict[str, Callable[..., EmbeddingModel]]] = {}

    @classmethod
    def register_chat(cls, model_type: str, creator: Callable[..., ChatModel]) -> None:
        """Register a ChatModel implementation."""
        cls._chat_registry[model_type] = creator

    @classmethod
    def register_embedding(
        cls, model_type: str, creator: Callable[..., EmbeddingModel]
    ) -> None:
        """Register an EmbeddingModel implementation."""
        cls._embedding_registry[model_type] = creator

    @classmethod
    def create_chat_model(cls, model_type: str, **kwargs: Any) -> ChatModel:
        """
        Create a ChatModel instance.

        Args:
            model_type: The type of ChatModel to create.
            **kwargs: Additional keyword arguments for the ChatModel constructor.

        Returns
        -------
            A ChatModel instance.
        """
        if model_type not in cls._chat_registry:
            msg = f"ChatMOdel implementation '{model_type}' is not registered."
            raise ValueError(msg)
        return cls._chat_registry[model_type](**kwargs)

    @classmethod
    def create_embedding_model(cls, model_type: str, **kwargs: Any) -> EmbeddingModel:
        """
        Create an EmbeddingModel instance.

        Args:
            model_type: The type of EmbeddingModel to create.
            **kwargs: Additional keyword arguments for the EmbeddingLLM constructor.

        Returns
        -------
            An EmbeddingLLM instance.
        """
        if model_type not in cls._embedding_registry:
            msg = f"EmbeddingModel implementation '{model_type}' is not registered."
            raise ValueError(msg)
        return cls._embedding_registry[model_type](**kwargs)

    @classmethod
    def get_chat_models(cls) -> list[str]:
        """Get the registered ChatModel implementations."""
        return list(cls._chat_registry.keys())

    @classmethod
    def get_embedding_models(cls) -> list[str]:
        """Get the registered EmbeddingModel implementations."""
        return list(cls._embedding_registry.keys())

    @classmethod
    def is_supported_chat_model(cls, model_type: str) -> bool:
        """Check if the given model type is supported."""
        return model_type in cls._chat_registry

    @classmethod
    def is_supported_embedding_model(cls, model_type: str) -> bool:
        """Check if the given model type is supported."""
        return model_type in cls._embedding_registry

    @classmethod
    def is_supported_model(cls, model_type: str) -> bool:
        """Check if the given model type is supported."""
        return cls.is_supported_chat_model(
            model_type
        ) or cls.is_supported_embedding_model(model_type)


# --- Register default implementations ---
ModelFactory.register_chat(
    ModelType.AzureOpenAIChat, lambda **kwargs: AzureOpenAIChatFNLLM(**kwargs)
)
ModelFactory.register_chat(
    ModelType.OpenAIChat, lambda **kwargs: OpenAIChatFNLLM(**kwargs)
)

ModelFactory.register_embedding(
    ModelType.AzureOpenAIEmbedding, lambda **kwargs: AzureOpenAIEmbeddingFNLLM(**kwargs)
)
ModelFactory.register_embedding(
    ModelType.OpenAIEmbedding, lambda **kwargs: OpenAIEmbeddingFNLLM(**kwargs)
)
