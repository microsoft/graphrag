# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Singleton LLM Manager for ChatLLM and EmbeddingsLLM instances.

This manager lets you register chat and embeddings LLMs independently.
It leverages the LLMFactory for instantiation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typing_extensions import Self

from graphrag.llm.factory import LLMFactory

if TYPE_CHECKING:
    from graphrag.llm.protocol import ChatLLM, EmbeddingLLM


class LLMManager:
    """Singleton manager for LLM instances."""

    _instance: LLMManager | None = None

    def __new__(cls: type[Self]) -> Self:
        """Create a new instance of LLMManager if it does not exist."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # Avoid reinitialization in the singleton.
        if not hasattr(self, "_initialized"):
            self.chat_llms: dict[str, ChatLLM] = {}
            self.embedding_llms: dict[str, EmbeddingLLM] = {}
            self._initialized = True

    @classmethod
    def get_instance(cls) -> LLMManager:
        """Return the singleton instance of LLMManager."""
        return cls.__new__(cls)

    def register_chat(self, name: str, model_type: str, **chat_kwargs: Any) -> ChatLLM:
        """
        Register a ChatLLM instance under a unique name.

        Args:
            name: Unique identifier for the ChatLLM instance.
            model_type: Key for the ChatLLM implementation in LLMFactory.
            **chat_kwargs: Additional parameters for instantiation.
        """
        chat_kwargs["name"] = name
        self.chat_llms[name] = LLMFactory.create_chat_llm(model_type, **chat_kwargs)
        return self.chat_llms[name]

    def register_embedding(
        self, name: str, model_type: str, **embedding_kwargs: Any
    ) -> EmbeddingLLM:
        """
        Register an EmbeddingsLLM instance under a unique name.

        Args:
            name: Unique identifier for the EmbeddingsLLM instance.
            embedding_key: Key for the EmbeddingsLLM implementation in LLMFactory.
            **embedding_kwargs: Additional parameters for instantiation.
        """
        embedding_kwargs["name"] = name
        self.embedding_llms[name] = LLMFactory.create_embedding_llm(
            model_type, **embedding_kwargs
        )
        return self.embedding_llms[name]

    def get_chat_llm(self, name: str) -> ChatLLM | None:
        """
        Retrieve the ChatLLM instance registered under the given name.

        Raises
        ------
            ValueError: If no ChatLLM is registered under the name.
        """
        if name not in self.chat_llms:
            msg = f"No ChatLLM registered under the name '{name}'."
            raise ValueError(msg)
        return self.chat_llms[name]

    def get_embedding_llm(self, name: str) -> EmbeddingLLM | None:
        """
        Retrieve the EmbeddingsLLM instance registered under the given name.

        Raises
        ------
            ValueError: If no EmbeddingsLLM is registered under the name.
        """
        if name not in self.embedding_llms:
            msg = f"No EmbeddingsLLM registered under the name '{name}'."
            raise ValueError(msg)
        return self.embedding_llms[name]

    def get_or_create_chat_llm(
        self, name: str, model_type: str, **chat_kwargs: Any
    ) -> ChatLLM:
        """
        Retrieve the ChatLLM instance registered under the given name.

        If the ChatLLM does not exist, it is created and registered.

        Args:
            name: Unique identifier for the ChatLLM instance.
            model_type: Key for the ChatLLM implementation in LLMFactory.
            **chat_kwargs: Additional parameters for instantiation.
        """
        if name not in self.chat_llms:
            return self.register_chat(name, model_type, **chat_kwargs)
        return self.chat_llms[name]

    def get_or_create_embedding_llm(
        self, name: str, model_type: str, **embedding_kwargs: Any
    ) -> EmbeddingLLM:
        """
        Retrieve the EmbeddingsLLM instance registered under the given name.

        If the EmbeddingsLLM does not exist, it is created and registered.

        Args:
            name: Unique identifier for the EmbeddingsLLM instance.
            model_type: Key for the EmbeddingsLLM implementation in LLMFactory.
            **embedding_kwargs: Additional parameters for instantiation.
        """
        if name not in self.embedding_llms:
            return self.register_embedding(name, model_type, **embedding_kwargs)
        return self.embedding_llms[name]

    def remove_chat(self, name: str) -> None:
        """Remove the ChatLLM instance registered under the given name."""
        self.chat_llms.pop(name, None)

    def remove_embedding(self, name: str) -> None:
        """Remove the EmbeddingsLLM instance registered under the given name."""
        self.embedding_llms.pop(name, None)

    def list_chat_llms(self) -> dict[str, ChatLLM]:
        """Return a copy of all registered ChatLLM instances."""
        return dict(self.chat_llms)

    def list_embedding_llms(self) -> dict[str, EmbeddingLLM]:
        """Return a copy of all registered EmbeddingsLLM instances."""
        return dict(self.embedding_llms)
