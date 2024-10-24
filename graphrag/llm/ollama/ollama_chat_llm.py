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
            **(kwargs.get("model_parameters") or {}),
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
        pass
