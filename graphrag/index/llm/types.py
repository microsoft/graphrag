# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""A module containing the 'LLMtype' model."""

from collections.abc import Callable
from enum import Enum
from typing import TypeAlias

TextSplitter: TypeAlias = Callable[[str], list[str]]
TextListSplitter: TypeAlias = Callable[[list[str]], list[str]]


class LLMType(str, Enum):
    """LLMType enum class definition."""

    # Embeddings
    OpenAIEmbedding = "openai_embedding"
    AzureOpenAIEmbedding = "azure_openai_embedding"

    # Raw Completion
    OpenAI = "openai"
    AzureOpenAI = "azure_openai"

    # Chat Completion
    OpenAIChat = "openai_chat"
    AzureOpenAIChat = "azure_openai_chat"

    # Debug
    StaticResponse = "static_response"
