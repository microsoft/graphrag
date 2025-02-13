# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Singleton LLM Manager for ChatLLM and EmbeddingsLLM instances.

This manager lets you register chat and embeddings LLMs independently.
It leverages the LLMFactory for instantiation.
"""

from __future__ import annotations

from typing import  Any
from llm.protocols import ChatLLM, EmbeddingLLM
from llm.factory import LLMFactory


class LLMManager:
    """Singleton manager for LLM instances."""

    _instance: LLMManager | None = None

    def __new__(cls) -> LLMManager:
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
        """Returns the singleton instance of LLMManager."""
        return cls.__new__(cls)

    def register_chat(self, name: str, chat_key: str, **chat_kwargs: Any) -> None:
        """
        Registers a ChatLLM instance under a unique name.

        Args:
            name: Unique identifier for the ChatLLM instance.
            chat_key: Key for the ChatLLM implementation in LLMFactory.
            **chat_kwargs: Additional parameters for instantiation.
        """
        self.chat_llms[name] = LLMFactory.create_chat_llm(chat_key, **chat_kwargs)

    def register_embedding(self, name: str, embedding_key: str, **embedding_kwargs: Any) -> None:
        """
        Registers an EmbeddingsLLM instance under a unique name.

        Args:
            name: Unique identifier for the EmbeddingsLLM instance.
            embedding_key: Key for the EmbeddingsLLM implementation in LLMFactory.
            **embedding_kwargs: Additional parameters for instantiation.
        """
        self.embedding_llms[name] = LLMFactory.create_embedding_llm(embedding_key, **embedding_kwargs)

    def get_chat_llm(self, name: str) -> ChatLLM:
        """
        Retrieves the ChatLLM instance registered under the given name.
        
        Raises:
            ValueError: If no ChatLLM is registered under the name.
        """
        if name not in self.chat_llms:
            raise ValueError(f"No ChatLLM registered under name '{name}'.")
        return self.chat_llms[name]

    def get_embedding_llm(self, name: str) -> EmbeddingLLM:
        """
        Retrieves the EmbeddingsLLM instance registered under the given name.
        
        Raises:
            ValueError: If no EmbeddingsLLM is registered under the name.
        """
        if name not in self.embedding_llms:
            raise ValueError(f"No EmbeddingsLLM registered under name '{name}'.")
        return self.embedding_llms[name]

    def remove_chat(self, name: str) -> None:
        """Removes the ChatLLM instance registered under the given name."""
        self.chat_llms.pop(name, None)

    def remove_embedding(self, name: str) -> None:
        """Removes the EmbeddingsLLM instance registered under the given name."""
        self.embedding_llms.pop(name, None)

    def list_chat_llms(self) -> dict[str, ChatLLM]:
        """Returns a copy of all registered ChatLLM instances."""
        return {k: v for k, v in self.chat_llms.items()}

    def list_embedding_llms(self) -> dict[str, EmbeddingLLM]:
        """Returns a copy of all registered EmbeddingsLLM instances."""
        return {k: v for k, v in self.embedding_llms.items()}