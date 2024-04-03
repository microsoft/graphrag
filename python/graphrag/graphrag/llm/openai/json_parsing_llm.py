# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""An LLM that unpacks cached JSON responses."""

import json
import logging
from typing import cast

from typing_extensions import Unpack

from graphrag.llm.types import (
    LLM,
    CompletionInput,
    CompletionLLM,
    CompletionOutput,
    LLMInput,
    LLMOutput,
)

log = logging.getLogger(__name__)

UNPARSABLE_JSON = "Failed to parse JSON data"


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
            try:
                result.json = cast(dict, json.loads(result.output))
            except json.decoder.JSONDecodeError as e:
                log.error("Failed to parse JSON output:\n%s", result.output)  # noqa TRY400
                raise ValueError(UNPARSABLE_JSON) from e
        return result
