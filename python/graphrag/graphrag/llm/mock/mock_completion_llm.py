#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""LLM Static Response method definition."""
import logging

from typing_extensions import Unpack

from graphrag.llm.base import BaseLLM
from graphrag.llm.types import (
    CompletionInput,
    CompletionOutput,
    LLMInput,
)

log = logging.getLogger(__name__)


class MockCompletionLLM(
    BaseLLM[
        CompletionInput,
        CompletionOutput,
    ]
):
    """Mock Completion LLM for testing purposes."""

    def __init__(self, responses: list[str]):
        self.responses = responses

    async def _execute_llm(
        self,
        input: CompletionInput,
        **kwargs: Unpack[LLMInput],
    ) -> CompletionOutput:
        return self.responses.pop(0)
