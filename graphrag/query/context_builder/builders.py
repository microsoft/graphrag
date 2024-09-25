# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Base classes for global and local context builders."""

from abc import ABC, abstractmethod

import pandas as pd

from graphrag.query.context_builder.conversation_history import (
    ConversationHistory,
)


class GlobalContextBuilder(ABC):
    """Base class for global-search context builders."""

    llm_calls: int = 0
    """The number of LLM calls made."""

    prompt_tokens: int = 0
    """The number of prompt tokens used in LLM calls."""

    output_tokens: int = 0
    """The number of output tokens from LLM calls."""

    @abstractmethod
    async def build_context(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        **kwargs,
    ) -> tuple[str | list[str], dict[str, pd.DataFrame]]:
        """Build the context for the global search mode."""


class LocalContextBuilder(ABC):
    """Base class for local-search context builders."""

    llm_calls: int = 0
    """The number of LLM calls made."""

    prompt_tokens: int = 0
    """The number of tokens in the prompt."""

    output_tokens: int = 0
    """The number of output tokens from LLM calls."""

    @abstractmethod
    def build_context(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        **kwargs,
    ) -> tuple[str | list[str], dict[str, pd.DataFrame]]:
        """Build the context for the local search mode."""
