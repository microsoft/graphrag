# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""LLM Types."""

from typing import TypeAlias

from .llm import LLM

EmbeddingInput: TypeAlias = list[str]
EmbeddingOutput: TypeAlias = list[list[float]]
CompletionInput: TypeAlias = str
CompletionOutput: TypeAlias = str

EmbeddingLLM: TypeAlias = LLM[EmbeddingInput, EmbeddingOutput]
CompletionLLM: TypeAlias = LLM[CompletionInput, CompletionOutput]
