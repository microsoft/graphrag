# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""LLM Manager singleton."""

from functools import cache

from fnllm import ChatLLM, EmbeddingsLLM


@cache
class ChatLLMSingleton:
    """A singleton class for the chat LLM instances."""

    def __init__(self):
        self.llm_dict = {}

    def set_llm(self, name, llm):
        """Add an LLM to the dictionary."""
        self.llm_dict[name] = llm

    def get_llm(self, name) -> ChatLLM | None:
        """Get an LLM from the dictionary."""
        return self.llm_dict.get(name)


@cache
class EmbeddingsLLMSingleton:
    """A singleton class for the embeddings LLM instances."""

    def __init__(self):
        self.llm_dict = {}

    def set_llm(self, name, llm):
        """Add an LLM to the dictionary."""
        self.llm_dict[name] = llm

    def get_llm(self, name) -> EmbeddingsLLM | None:
        """Get an LLM from the dictionary."""
        return self.llm_dict.get(name)
