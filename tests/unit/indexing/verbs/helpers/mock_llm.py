# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
from pydantic import BaseModel

from graphrag.llm.manager import LLMManager
from graphrag.llm.protocol.base import ChatLLM


def create_mock_llm(responses: list[str | BaseModel], name: str = "mock") -> ChatLLM:
    """Creates a mock LLM that returns the given responses."""
    return LLMManager().get_or_create_chat_llm(name, "mock_chat", responses=responses)
