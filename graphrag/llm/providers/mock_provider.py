# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing mock model provider definitions."""

from typing import Any

from pydantic import BaseModel

from graphrag.config.models.language_model_config import LanguageModelConfig
from graphrag.llm.response.base import BaseLLMOutput, BaseLLMResponse, LLMResponse


class MockChatLLM:
    """A mock chat LLM provider."""

    def __init__(
        self,
        responses: list[str | BaseModel] | None,
        config: LanguageModelConfig | None,
        json: bool = False,
    ):
        self.responses = config.responses if config and config.responses else responses
        self.response_index = 0

    async def chat(
        self,
        prompt: str,
        **kwargs,
    ) -> LLMResponse:
        """Return the next response in the list."""
        if not self.responses:
            return BaseLLMResponse(output=BaseLLMOutput(content=""))

        response = self.responses[self.response_index % len(self.responses)]
        self.response_index += 1

        parsed_json = response if isinstance(response, BaseModel) else None
        response = (
            response.model_dump_json() if isinstance(response, BaseModel) else response
        )

        return BaseLLMResponse(
            output=BaseLLMOutput(content=response),
            parsed_response=parsed_json,
        )


class MockEmbeddingLLM:
    """A mock embedding LLM provider."""

    async def embed(self, text: str | list[str], **kwargs: Any) -> list[list[float]]:
        """Generate an embedding for the input text."""
        return [[0.0, 0.0, 0.0]]
