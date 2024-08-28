# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Base classes for search algos."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any

import pandas as pd
import tiktoken

from graphrag.query.context_builder.builders import (
    GlobalContextBuilder,
    LocalContextBuilder,
)
from graphrag.query.context_builder.conversation_history import (
    ConversationHistory,
)
from graphrag.query.llm.base import BaseLLM


@dataclass
class SearchResult:
    """A Structured Search Result."""

    response: str | dict[str, Any] | list[dict[str, Any]]
    context_data: str | list[pd.DataFrame] | dict[str, pd.DataFrame]
    # actual text strings that are in the context window, built from context_data
    context_text: str | list[str] | dict[str, str]
    completion_time: float
    llm_calls: int
    prompt_tokens: int


class BaseSearch(ABC):
    """The Base Search implementation."""

    def __init__(
        self,
        llm: BaseLLM,
        context_builder: GlobalContextBuilder | LocalContextBuilder,
        token_encoder: tiktoken.Encoding | None = None,
        llm_params: dict[str, Any] | None = None,
        context_builder_params: dict[str, Any] | None = None,
    ):
        self.llm = llm
        self.context_builder = context_builder
        self.token_encoder = token_encoder
        self.llm_params = llm_params or {}
        self.context_builder_params = context_builder_params or {}

    @abstractmethod
    def search(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        **kwargs,
    ) -> SearchResult:
        """Search for the given query."""

    @abstractmethod
    async def asearch(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        **kwargs,
    ) -> SearchResult:
        """Search for the given query asynchronously."""

    @abstractmethod
    def astream_search(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream search for the given query."""
