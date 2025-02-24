# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
from pydantic import BaseModel

from graphrag.language_model.manager import ModelManager
from graphrag.language_model.protocol.base import ChatModel


def create_mock_llm(responses: list[str | BaseModel], name: str = "mock") -> ChatModel:
    """Creates a mock LLM that returns the given responses."""
    return ModelManager().get_or_create_chat_model(
        name, "mock_chat", responses=responses
    )
