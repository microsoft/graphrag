#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""Mock LLM Implementations."""

from .mock_chat_llm import MockChatLLM
from .mock_completion_llm import MockCompletionLLM

__all__ = [
    "MockCompletionLLM",
    "MockChatLLM",
]
