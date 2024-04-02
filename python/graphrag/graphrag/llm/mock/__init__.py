# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Mock LLM Implementations."""

from .mock_chat_llm import MockChatLLM
from .mock_completion_llm import MockCompletionLLM

__all__ = [
    "MockChatLLM",
    "MockCompletionLLM",
]
