# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing mock model provider definitions."""

from typing import Any

from pydantic import BaseModel

from graphrag.config.models.language_model_config import LanguageModelConfig
from graphrag.language_model.response.base import (
    BaseModelOutput,
    BaseModelResponse,
    ModelResponse,
)


class MockChatLLM:
    """A mock chat LLM provider."""

    def __init__(
        self,
        responses: list[str | BaseModel] | None = None,
        config: LanguageModelConfig | None = None,
        json: bool = False,
        **kwargs: Any,
    ):
        self.responses = config.responses if config and config.responses else responses
        self.response_index = 0

    async def chat(
        self,
        prompt: str,
        **kwargs,
    ) -> ModelResponse:
        """Return the next response in the list."""
        if not self.responses:
            return BaseModelResponse(output=BaseModelOutput(content=""))

        response = self.responses[self.response_index % len(self.responses)]
        self.response_index += 1

        parsed_json = response if isinstance(response, BaseModel) else None
        response = (
            response.model_dump_json() if isinstance(response, BaseModel) else response
        )

        return BaseModelResponse(
            output=BaseModelOutput(content=response),
            parsed_response=parsed_json,
        )


class MockEmbeddingLLM:
    """A mock embedding LLM provider."""

    def __init__(self, **kwargs: Any):
        pass

    async def embed(self, text: str | list[str], **kwargs: Any) -> list[list[float]]:
        """Generate an embedding for the input text."""
        if isinstance(text, str):
            return [[1.0, 1.0, 1.0]]
        return [[1.0, 1.0, 1.0] for _ in text]
