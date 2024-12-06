# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""A mock LLM that returns the given responses."""

from dataclasses import dataclass
from typing import Any, cast

from fnllm import ChatLLM, LLMInput, LLMOutput
from fnllm.types.generics import THistoryEntry, TJsonModel, TModelParameters
from pydantic import BaseModel
from typing_extensions import Unpack


@dataclass
class ContentResponse:
    """A mock content-only response."""

    content: str


class MockChatLLM(ChatLLM):
    """A mock LLM that returns the given responses."""

    def __init__(self, responses: list[str | BaseModel], json: bool = False):
        self.responses = responses
        self.response_index = 0

    async def __call__(
        self,
        prompt: str,
        **kwargs: Unpack[LLMInput[TJsonModel, THistoryEntry, TModelParameters]],
    ) -> LLMOutput[Any, TJsonModel, THistoryEntry]:
        """Return the next response in the list."""
        response = self.responses[self.response_index % len(self.responses)]
        self.response_index += 1

        parsed_json = response if isinstance(response, BaseModel) else None
        response = (
            response.model_dump_json() if isinstance(response, BaseModel) else response
        )

        return LLMOutput(
            output=ContentResponse(content=response),
            parsed_json=cast("TJsonModel", parsed_json),
        )

    def child(self, name):
        """Return a new mock LLM."""
        raise NotImplementedError
