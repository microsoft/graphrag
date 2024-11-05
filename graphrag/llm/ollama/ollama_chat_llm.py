# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Chat-based language model."""

import logging

from typing_extensions import Unpack

from graphrag.llm.base import BaseLLM
from graphrag.llm.types import (
    CompletionInput,
    CompletionOutput,
    LLMInput,
    LLMOutput,
)
from graphrag.llm.utils import try_parse_json_object

from .ollama_configuration import OllamaConfiguration
from .types import OllamaClientType

log = logging.getLogger(__name__)

_MAX_GENERATION_RETRIES = 3
FAILED_TO_CREATE_JSON_ERROR = "Failed to generate valid JSON output"


class OllamaChatLLM(BaseLLM[CompletionInput, CompletionOutput]):
    """A Chat-based LLM."""

    _client: OllamaClientType
    _configuration: OllamaConfiguration

    def __init__(self, client: OllamaClientType, configuration: OllamaConfiguration):
        self.client = client
        self.configuration = configuration

    async def _execute_llm(
        self, input: CompletionInput, **kwargs: Unpack[LLMInput]
    ) -> CompletionOutput | None:
        args = {
            **self.configuration.get_chat_cache_args(),
        }
        history = kwargs.get("history") or []
        messages = [
            *history,
            {"role": "user", "content": input},
        ]
        completion = await self.client.chat(
            messages=messages, **args
        )
        return completion["message"]["content"]

    async def _invoke_json(
            self,
            input: CompletionInput,
            **kwargs: Unpack[LLMInput],
    ) -> LLMOutput[CompletionOutput]:
        """Generate JSON output."""
        name = kwargs.get("name") or "unknown"
        is_response_valid = kwargs.get("is_response_valid") or (lambda _x: True)

        async def generate(
                attempt: int | None = None,
        ) -> LLMOutput[CompletionOutput]:
            call_name = name if attempt is None else f"{name}@{attempt}"
            result = await self._invoke(input, **{**kwargs, "name": call_name})
            print("output:\n", result)
            output, json_output = try_parse_json_object(result.output or "")

            return LLMOutput[CompletionOutput](
                output=output,
                json=json_output,
                history=result.history,
            )

        def is_valid(x: dict | None) -> bool:
            return x is not None and is_response_valid(x)

        result = await generate()
        retry = 0
        while not is_valid(result.json) and retry < _MAX_GENERATION_RETRIES:
            result = await generate(retry)
            retry += 1

        if is_valid(result.json):
            return result

        error_msg = f"{FAILED_TO_CREATE_JSON_ERROR} - Faulty JSON: {result.json!s}"
        raise RuntimeError(error_msg)
