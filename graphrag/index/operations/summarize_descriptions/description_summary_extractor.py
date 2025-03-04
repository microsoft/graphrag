# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'GraphExtractionResult' and 'GraphExtractor' models."""

import json
from dataclasses import dataclass

from graphrag.index.typing.error_handler import ErrorHandlerFn
from graphrag.index.utils.tokens import num_tokens_from_string
from graphrag.language_model.protocol.base import ChatModel
from graphrag.prompts.index.summarize_descriptions import SUMMARIZE_PROMPT

# Max token size for input prompts
DEFAULT_MAX_INPUT_TOKENS = 4_000
# Max token count for LLM answers
DEFAULT_MAX_SUMMARY_LENGTH = 500


@dataclass
class SummarizationResult:
    """Unipartite graph extraction result class definition."""

    id: str | tuple[str, str]
    description: str


class SummarizeExtractor:
    """Unipartite graph extractor class definition."""

    _model: ChatModel
    _entity_name_key: str
    _input_descriptions_key: str
    _summarization_prompt: str
    _on_error: ErrorHandlerFn
    _max_summary_length: int
    _max_input_tokens: int

    def __init__(
        self,
        model_invoker: ChatModel,
        entity_name_key: str | None = None,
        input_descriptions_key: str | None = None,
        summarization_prompt: str | None = None,
        on_error: ErrorHandlerFn | None = None,
        max_summary_length: int | None = None,
        max_input_tokens: int | None = None,
    ):
        """Init method definition."""
        # TODO: streamline construction
        self._model = model_invoker
        self._entity_name_key = entity_name_key or "entity_name"
        self._input_descriptions_key = input_descriptions_key or "description_list"

        self._summarization_prompt = summarization_prompt or SUMMARIZE_PROMPT
        self._on_error = on_error or (lambda _e, _s, _d: None)
        self._max_summary_length = max_summary_length or DEFAULT_MAX_SUMMARY_LENGTH
        self._max_input_tokens = max_input_tokens or DEFAULT_MAX_INPUT_TOKENS

    async def __call__(
        self,
        id: str | tuple[str, str],
        descriptions: list[str],
    ) -> SummarizationResult:
        """Call method definition."""
        result = ""
        if len(descriptions) == 0:
            result = ""
        elif len(descriptions) == 1:
            result = descriptions[0]
        else:
            result = await self._summarize_descriptions(id, descriptions)

        return SummarizationResult(
            id=id,
            description=result or "",
        )

    async def _summarize_descriptions(
        self, id: str | tuple[str, str], descriptions: list[str]
    ) -> str:
        """Summarize descriptions into a single description."""
        sorted_id = sorted(id) if isinstance(id, list) else id

        # Safety check, should always be a list
        if not isinstance(descriptions, list):
            descriptions = [descriptions]

        # Sort description lists
        if len(descriptions) > 1:
            descriptions = sorted(descriptions)

        # Iterate over descriptions, adding all until the max input tokens is reached
        usable_tokens = self._max_input_tokens - num_tokens_from_string(
            self._summarization_prompt
        )
        descriptions_collected = []
        result = ""

        for i, description in enumerate(descriptions):
            usable_tokens -= num_tokens_from_string(description)
            descriptions_collected.append(description)

            # If buffer is full, or all descriptions have been added, summarize
            if (usable_tokens < 0 and len(descriptions_collected) > 1) or (
                i == len(descriptions) - 1
            ):
                # Calculate result (final or partial)
                result = await self._summarize_descriptions_with_llm(
                    sorted_id, descriptions_collected
                )

                # If we go for another loop, reset values to new
                if i != len(descriptions) - 1:
                    descriptions_collected = [result]
                    usable_tokens = (
                        self._max_input_tokens
                        - num_tokens_from_string(self._summarization_prompt)
                        - num_tokens_from_string(result)
                    )

        return result

    async def _summarize_descriptions_with_llm(
        self, id: str | tuple[str, str] | list[str], descriptions: list[str]
    ):
        """Summarize descriptions using the LLM."""
        response = await self._model.achat(
            self._summarization_prompt.format(**{
                self._entity_name_key: json.dumps(id, ensure_ascii=False),
                self._input_descriptions_key: json.dumps(
                    sorted(descriptions), ensure_ascii=False
                ),
            }),
            name="summarize",
            model_parameters={"max_tokens": self._max_summary_length},
        )
        # Calculate result
        return str(response.output.content)
