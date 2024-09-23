# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A mock ChatLLM that returns the given responses."""

from typing_extensions import Unpack

from graphrag.llm.base import BaseLLM
from graphrag.llm.types import (
    CompletionInput,
    CompletionOutput,
    LLMInput,
    LLMOutput,
)


class MockChatLLM(
    BaseLLM[
        CompletionInput,
        CompletionOutput,
    ]
):
    """A mock LLM that returns the given responses."""

    responses: list[str]
    i: int = 0

    def __init__(self, responses: list[str]):
        self.i = 0
        self.responses = responses

    def _create_output(
        self,
        output: CompletionOutput | None,
        **kwargs: Unpack[LLMInput],
    ) -> LLMOutput[CompletionOutput]:
        history = kwargs.get("history") or []
        return LLMOutput[CompletionOutput](
            output=output, history=[*history, {"content": output}]
        )

    async def _execute_llm(
        self,
        input: CompletionInput,
        **kwargs: Unpack[LLMInput],
    ) -> CompletionOutput:
        if self.i >= len(self.responses):
            msg = f"No more responses, requested {self.i} but only have {len(self.responses)}"
            raise ValueError(msg)
        response = self.responses[self.i]
        self.i += 1
        return response
