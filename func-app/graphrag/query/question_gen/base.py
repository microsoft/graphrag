# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Base classes for generating questions based on previously asked questions and most recent context data."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import tiktoken

from graphrag.query.context_builder.builders import (
    GlobalContextBuilder,
    LocalContextBuilder,
)
from graphrag.query.llm.base import BaseLLM


@dataclass
class QuestionResult:
    """A Structured Question Result."""

    response: list[str]
    context_data: str | dict[str, Any]
    completion_time: float
    llm_calls: int
    prompt_tokens: int


class BaseQuestionGen(ABC):
    """The Base Question Gen implementation."""

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
    def generate(
        self,
        question_history: list[str],
        context_data: str | None,
        question_count: int,
        **kwargs,
    ) -> QuestionResult:
        """Generate questions."""

    @abstractmethod
    async def agenerate(
        self,
        question_history: list[str],
        context_data: str | None,
        question_count: int,
        **kwargs,
    ) -> QuestionResult:
        """Generate questions asynchronously."""
