# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Chat-based language model."""

from typing_extensions import Unpack

from graphrag.llm.types import (
    LLM,
    CompletionInput,
    CompletionLLM,
    CompletionOutput,
    LLMInput,
    LLMOutput,
)


class OpenAIHistoryTrackingLLM(LLM[CompletionInput, CompletionOutput]):
    """An OpenAI History-Tracking LLM."""

    _delegate: CompletionLLM

    def __init__(self, delegate: CompletionLLM):
        self._delegate = delegate

    async def __call__(
        self,
        input: CompletionInput,
        **kwargs: Unpack[LLMInput],
    ) -> LLMOutput[CompletionOutput]:
        """Call the LLM."""
        history = kwargs.get("history") or []
        output = await self._delegate(input, **kwargs)
        return LLMOutput(
            output=output.output,
            json=output.json,
            history=[*history, {"role": "system", "content": output.output}],
        )
