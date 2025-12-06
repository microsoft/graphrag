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


@dataclass
class LLMParameters:
    """A class to hold LLM call parameters."""

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

    @abstractmethod
    async def build_context_chunks(
        self,
        query: str,
        **kwargs,
    ) -> str | list[str]:
        """Build the context chunks for the global search mode."""

    @abstractmethod
    async def build_context_records(
        self,
        query: str,
        **kwargs,
    ) -> dict[str, pd.DataFrame]:
        """Build the context records for the global search mode."""


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

    @abstractmethod
    def build_context_chunks(
        self,
        query: str,
        **kwargs,
    ) -> str:
        """Build the context chunks for the local search mode."""

    @abstractmethod
    def build_context_records(
        self,
        query: str,
        **kwargs,
    ) -> dict[str, pd.DataFrame]:
        """Build the context records for the local search mode."""


class DRIFTContextBuilder(ABC):
    """Base class for DRIFT-search context builders."""

    @abstractmethod
    async def build_context(
        self,
        query: str,
        **kwargs,
    ) -> tuple[pd.DataFrame, dict[str, int]]:
        """Build the context for the primer search actions."""


class BasicContextBuilder(ABC):
    """Base class for basic-search context builders."""

    @abstractmethod
    def build_context_records(
        self,
        query: str,
        **kwargs,
    ) -> dict[str, pd.DataFrame]:
        """Build the context records for the basic search mode."""

    @abstractmethod
    def get_llm_values(self) -> LLMParameters:
        """Get the LLM call values."""
