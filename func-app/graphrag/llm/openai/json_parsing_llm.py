# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""An LLM that unpacks cached JSON responses."""

from typing_extensions import Unpack

from graphrag.llm.types import (
    LLM,
    CompletionInput,
    CompletionLLM,
    CompletionOutput,
    LLMInput,
    LLMOutput,
)

from .utils import try_parse_json_object


class JsonParsingLLM(LLM[CompletionInput, CompletionOutput]):
    """An OpenAI History-Tracking LLM."""

    _delegate: CompletionLLM

    def __init__(self, delegate: CompletionLLM):
        self._delegate = delegate

    async def __call__(
        self,
        input: CompletionInput,
        **kwargs: Unpack[LLMInput],
    ) -> LLMOutput[CompletionOutput]:
        """Call the LLM with the input and kwargs."""
        result = await self._delegate(input, **kwargs)
        if kwargs.get("json") and result.json is None and result.output is not None:
            _, parsed_json = try_parse_json_object(result.output)
            result.json = parsed_json
        return result
