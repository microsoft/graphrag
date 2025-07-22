# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Base classes for search algos."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

import pandas as pd
import tiktoken

from graphrag.language_model.protocol.base import ChatModel
from graphrag.query.context_builder.builders import (
    BasicContextBuilder,
    DRIFTContextBuilder,
    GlobalContextBuilder,
    LocalContextBuilder,
)
from graphrag.query.context_builder.conversation_history import (
    ConversationHistory,
)


@dataclass
class SearchResult:
    """A Structured Search Result."""

    response: str | dict[str, Any] | list[dict[str, Any]]
    context_data: str | list[pd.DataFrame] | dict[str, pd.DataFrame]
    # actual text strings that are in the context window, built from context_data
    context_text: str | list[str] | dict[str, str]
    completion_time: float
    # total LLM calls and token usage
    llm_calls: int
    prompt_tokens: int
    output_tokens: int
    # breakdown of LLM calls and token usage
    llm_calls_categories: dict[str, int] | None = None
    prompt_tokens_categories: dict[str, int] | None = None
    output_tokens_categories: dict[str, int] | None = None


T = TypeVar(
    "T",
    GlobalContextBuilder,
    LocalContextBuilder,
    DRIFTContextBuilder,
    BasicContextBuilder,
)


class BaseSearch(ABC, Generic[T]):
    """The Base Search implementation."""

    def __init__(
        self,
        model: ChatModel,
        context_builder: T,
        token_encoder: tiktoken.Encoding | None = None,
        model_params: dict[str, Any] | None = None,
        context_builder_params: dict[str, Any] | None = None,
    ):
        self.model = model
        self.context_builder = context_builder
        self.token_encoder = token_encoder
        self.model_params = model_params or {}
        self.context_builder_params = context_builder_params or {}

    @abstractmethod
    async def search(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        **kwargs,
    ) -> SearchResult:
        """Search for the given query asynchronously."""
        msg = "Subclasses must implement this method"
        raise NotImplementedError(msg)

    @abstractmethod
    async def stream_search(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream search for the given query."""
        yield ""  # This makes it an async generator.
        msg = "Subclasses must implement this method"
        raise NotImplementedError(msg)
