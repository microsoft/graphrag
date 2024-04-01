#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""A module containing 'GraphExtractionResult' and 'GraphExtractor' models."""

import json
from dataclasses import dataclass

from graphrag.index.typing import ErrorHandlerFn
from graphrag.llm import CompletionLLM

from .prompts import SUMMARIZE_PROMPT


@dataclass
class SummarizationResult:
    """Unipartite graph extraction result class definition."""

    items: str | tuple[str, str]
    description: str


class SummarizeExtractor:
    """Unipartite graph extractor class definition."""

    _llm: CompletionLLM
    _entity_name_key: str
    _input_descriptions_key: str
    _summarization_prompt: str
    _on_error: ErrorHandlerFn
    _max_summary_length: int

    def __init__(
        self,
        llm_invoker: CompletionLLM,
        entity_name_key: str | None = None,
        input_descriptions_key: str | None = None,
        summarization_prompt: str | None = None,
        on_error: ErrorHandlerFn | None = None,
        max_summary_length: int | None = None,
    ):
        """Init method definition."""
        # TODO: streamline construction
        self._llm = llm_invoker
        self._entity_name_key = entity_name_key or "entity_name"
        self._input_descriptions_key = input_descriptions_key or "description_list"

        self._summarization_prompt = summarization_prompt or SUMMARIZE_PROMPT
        self._on_error = on_error or (lambda _e, _s, _d: None)
        self._max_summary_length = max_summary_length or 500

    async def __call__(
        self,
        items: str | tuple[str, str],
        descriptions: list[str],
    ) -> SummarizationResult:
        """Call method definition."""
        result = ""
        if len(descriptions) == 0:
            result = ""
        if len(descriptions) == 1:
            result = descriptions[0]
        else:
            sorted_items = sorted(items) if isinstance(items, list) else items

            # Safety check, should always be a list
            if not isinstance(descriptions, list):
                descriptions = [descriptions]

            response = await self._llm(
                self._summarization_prompt,
                name="summarize",
                variables={
                    self._entity_name_key: json.dumps(sorted_items),
                    self._input_descriptions_key: json.dumps(sorted(descriptions)),
                },
                model_parameters={"max_tokens": self._max_summary_length},
            )
            result = response.output

        return SummarizationResult(
            items=items,
            description=result or "",
        )
