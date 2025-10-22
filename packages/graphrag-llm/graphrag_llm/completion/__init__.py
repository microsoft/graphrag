# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Completion module for graphrag-llm."""

from graphrag_llm.completion.completion import LLMCompletion
from graphrag_llm.completion.completion_factory import (
    create_completion,
    register_completion,
)

__all__ = [
    "LLMCompletion",
    "create_completion",
    "register_completion",
]
