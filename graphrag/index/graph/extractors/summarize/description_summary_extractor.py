# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'GraphExtractionResult' and 'GraphExtractor' models."""

import json
from dataclasses import dataclass

import tiktoken

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
    _encoding_model: str
    _truncate: bool

    def __init__(
        self,
        llm_invoker: CompletionLLM,
        entity_name_key: str | None = None,
        input_descriptions_key: str | None = None,
        summarization_prompt: str | None = None,
        on_error: ErrorHandlerFn | None = None,
        max_summary_length: int | None = None,
        truncate: bool = True,
    ):
        """Init method definition."""
        # TODO: streamline construction
        self._llm = llm_invoker
        self._entity_name_key = entity_name_key or "entity_name"
        self._input_descriptions_key = input_descriptions_key or "description_list"

        self._summarization_prompt = summarization_prompt or SUMMARIZE_PROMPT
        self._on_error = on_error or (lambda _e, _s, _d: None)
        self._max_summary_length = max_summary_length or 500

        self._encoding_model = self._llm._delegate._delegate._delegate._config.encoding_model
        self._truncate = truncate
        
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
            
            # Truncation of descriptions
            if self._truncate:
                max_description_length = 126000 #Buffer for different tokenizers
                encoder = tiktoken.get_encoding(self._encoding_model)
                max_description_length -= len(encoder.encode(self._summarization_prompt))
                max_description_length -= len(encoder.encode(json.dumps(sorted_items)))
                descriptions = sorted(descriptions)
                description_lengths = [len(encoder.encode(x)) + 3 for x in descriptions]
                if sum(description_lengths) > max_description_length:
                    new_descriptions = []
                    while True:
                        if sum(description_lengths[:len(new_descriptions)+1]) > max_description_length:
                            break
                        new_descriptions += [descriptions[len(new_descriptions)]]
                    descriptions = new_descriptions

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
