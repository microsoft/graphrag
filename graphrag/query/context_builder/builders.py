# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Base classes for global and local context builders."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd

from graphrag.query.context_builder.conversation_history import (
    ConversationHistory,
)


@dataclass
class ContextBuilderResult:
    """A class to hold the results of the build_context."""

    context_chunks: str | list[str]
    context_records: dict[str, pd.DataFrame]
    llm_calls: int = 0
    prompt_tokens: int = 0
    output_tokens: int = 0


class GlobalContextBuilder(ABC):
    """Base class for global-search context builders."""

    @abstractmethod
    async def build_context(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        **kwargs,
    ) -> ContextBuilderResult:
        """Build the context for the global search mode."""


class LocalContextBuilder(ABC):
    """Base class for local-search context builders."""

    @abstractmethod
    def build_context(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        **kwargs,
    ) -> ContextBuilderResult:
        """Build the context for the local search mode."""


class DRIFTContextBuilder(ABC):
    """Base class for DRIFT-search context builders."""

    @abstractmethod
    def build_context(
        self,
        query: str,
        **kwargs,
    ) -> tuple[pd.DataFrame, dict[str, int]]:
        """Build the context for the primer search actions."""
