# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
from pydantic import BaseModel

from graphrag.config.models.language_model_config import LanguageModelConfig
from graphrag.language_model.manager import ModelManager


def create_mock_llm(
    responses: list[str | BaseModel], name: str = "mock"
) -> LanguageModelConfig:
    """Creates a mock LLM that returns the given responses."""
    return (
        ModelManager()
        .get_or_create_chat_model(name, "mock_chat", responses=responses)
        .config
    )
