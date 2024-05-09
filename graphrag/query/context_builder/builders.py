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

    @abstractmethod
    def build_context(
        self, conversation_history: ConversationHistory | None = None, **kwargs
    ) -> tuple[str | list[str], dict[str, pd.DataFrame]]:
        """Build the context for the global search mode."""


class LocalContextBuilder(ABC):
    """Base class for local-search context builders."""

    @abstractmethod
    def build_context(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        **kwargs,
    ) -> tuple[str | list[str], dict[str, pd.DataFrame]]:
        """Build the context for the local search mode."""
