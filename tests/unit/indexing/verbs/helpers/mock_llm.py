# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
from fnllm import LLM, LLMInput, LLMOutput
from fnllm.types.generics import THistoryEntry, TJsonModel, TModelParameters
from typing_extensions import Unpack


class MockChatLLM(LLM):
    def __init__(self, responses: list[str]):
        self.responses = responses
        self.response_index = 0

    async def __call__(
        self,
        prompt: str,
        **kwargs: Unpack[LLMInput[TJsonModel, THistoryEntry, TModelParameters]],
    ) -> LLMOutput[str, TJsonModel, THistoryEntry]:
        response = self.responses[self.response_index]
        self.response_index += 1
        return LLMOutput(output=response)


def create_mock_llm(
    responses: list[str],
) -> LLM:
    """Creates a mock LLM that returns the given responses."""
    return MockChatLLM(responses)
