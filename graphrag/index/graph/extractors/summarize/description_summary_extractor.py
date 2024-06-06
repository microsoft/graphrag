# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'GraphExtractionResult' and 'GraphExtractor' models."""

import json
from dataclasses import dataclass

from graphrag.index.typing import ErrorHandlerFn
from graphrag.index.utils.tokens import num_tokens_from_string
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
    _max_input_tokens: int

    def __init__(
        self,
        llm_invoker: CompletionLLM,
        entity_name_key: str | None = None,
        input_descriptions_key: str | None = None,
        summarization_prompt: str | None = None,
        on_error: ErrorHandlerFn | None = None,
        max_summary_length: int | None = None,
        max_input_tokens: int | None = None,
    ):
        """Init method definition."""
        # TODO: streamline construction
        self._llm = llm_invoker
        self._entity_name_key = entity_name_key or "entity_name"
        self._input_descriptions_key = input_descriptions_key or "description_list"

        self._summarization_prompt = summarization_prompt or SUMMARIZE_PROMPT
        self._on_error = on_error or (lambda _e, _s, _d: None)
        self._max_summary_length = max_summary_length or 500
        self._max_input_tokens = max_input_tokens or 4000

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

            # Iterate over descriptions, adding all until the max input tokens is reached
            usable_tokens = self._max_input_tokens - num_tokens_from_string(
                self._summarization_prompt
            )
            descriptions_collected = []

            for i, description in enumerate(descriptions):
                usable_tokens -= num_tokens_from_string(description)
                descriptions_collected.append(description)

                # If buffer is full, or all descriptions have been added, summarize
                if (usable_tokens < 0 and len(descriptions_collected) > 1) or (
                    i == len(descriptions) - 1
                ):
                    response = await self._llm(
                        self._summarization_prompt,
                        name="summarize",
                        variables={
                            self._entity_name_key: json.dumps(sorted_items),
                            self._input_descriptions_key: json.dumps(
                                sorted(descriptions)
                            ),
                        },
                        model_parameters={"max_tokens": self._max_summary_length},
                    )
                    # Calculate result (final or interim)
                    result = str(response.output)

                    # If we go for another loop, reset values to new
                    if i != len(descriptions) - 1:
                        descriptions_collected = [result]
                        usable_tokens = (
                            self._max_input_tokens
                            - num_tokens_from_string(self._summarization_prompt)
                            - num_tokens_from_string(result)
                        )

        return SummarizationResult(
            items=items,
            description=result or "",
        )
