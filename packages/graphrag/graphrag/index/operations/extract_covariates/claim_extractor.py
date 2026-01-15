# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'ClaimExtractorResult' and 'ClaimExtractor' models."""

import logging
import traceback
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from graphrag_llm.utils import (
    CompletionMessagesBuilder,
)

from graphrag.config.defaults import graphrag_config_defaults
from graphrag.index.typing.error_handler import ErrorHandlerFn
from graphrag.prompts.index.extract_claims import (
    CONTINUE_PROMPT,
    LOOP_PROMPT,
)

if TYPE_CHECKING:
    from graphrag_llm.completion import LLMCompletion
    from graphrag_llm.types import LLMCompletionResponse

INPUT_TEXT_KEY = "input_text"
INPUT_ENTITY_SPEC_KEY = "entity_specs"
INPUT_CLAIM_DESCRIPTION_KEY = "claim_description"
INPUT_RESOLVED_ENTITIES_KEY = "resolved_entities"
RECORD_DELIMITER_KEY = "record_delimiter"
COMPLETION_DELIMITER_KEY = "completion_delimiter"
TUPLE_DELIMITER = "<|>"
RECORD_DELIMITER = "##"
COMPLETION_DELIMITER = "<|COMPLETE|>"
logger = logging.getLogger(__name__)


@dataclass
class ClaimExtractorResult:
    """Claim extractor result class definition."""

    output: list[dict]
    source_docs: dict[str, Any]


class ClaimExtractor:
    """Claim extractor class definition."""

    _model: "LLMCompletion"
    _extraction_prompt: str
    _max_gleanings: int
    _on_error: ErrorHandlerFn

    def __init__(
        self,
        model: "LLMCompletion",
        extraction_prompt: str,
        max_gleanings: int | None = None,
        on_error: ErrorHandlerFn | None = None,
    ):
        """Init method definition."""
        self._model = model
        self._extraction_prompt = extraction_prompt
        self._max_gleanings = (
            max_gleanings
            if max_gleanings is not None
            else graphrag_config_defaults.extract_claims.max_gleanings
        )
        self._on_error = on_error or (lambda _e, _s, _d: None)

    async def __call__(
        self,
        texts,
        entity_spec,
        resolved_entities,
        claim_description,
    ) -> ClaimExtractorResult:
        """Call method definition."""
        source_doc_map = {}
        all_claims: list[dict] = []
        for doc_index, text in enumerate(texts):
            document_id = f"d{doc_index}"
            try:
                claims = await self._process_document(
                    text, claim_description, entity_spec
                )
                all_claims += [
                    self._clean_claim(c, document_id, resolved_entities) for c in claims
                ]
                source_doc_map[document_id] = text
            except Exception as e:
                logger.exception("error extracting claim")
                self._on_error(
                    e,
                    traceback.format_exc(),
                    {"doc_index": doc_index, "text": text},
                )
                continue

        return ClaimExtractorResult(
            output=all_claims,
            source_docs=source_doc_map,
        )

    def _clean_claim(
        self, claim: dict, document_id: str, resolved_entities: dict
    ) -> dict:
        # clean the parsed claims to remove any claims with status = False
        obj = claim.get("object_id", claim.get("object"))
        subject = claim.get("subject_id", claim.get("subject"))

        # If subject or object in resolved entities, then replace with resolved entity
        obj = resolved_entities.get(obj, obj)
        subject = resolved_entities.get(subject, subject)
        claim["object_id"] = obj
        claim["subject_id"] = subject
        return claim

    async def _process_document(
        self, text: str, claim_description: str, entity_spec: dict
    ) -> list[dict]:
        messages_builder = CompletionMessagesBuilder().add_user_message(
            self._extraction_prompt.format(**{
                INPUT_TEXT_KEY: text,
                INPUT_CLAIM_DESCRIPTION_KEY: claim_description,
                INPUT_ENTITY_SPEC_KEY: entity_spec,
            })
        )

        response: LLMCompletionResponse = await self._model.completion_async(
            messages=messages_builder.build(),
        )  # type: ignore
        results = response.content
        messages_builder.add_assistant_message(results)
        claims = results.strip().removesuffix(COMPLETION_DELIMITER)

        # if gleanings are specified, enter a loop to extract more claims
        # there are two exit criteria: (a) we hit the configured max, (b) the model says there are no more claims
        if self._max_gleanings > 0:
            for i in range(self._max_gleanings):
                messages_builder.add_user_message(CONTINUE_PROMPT)
                response: LLMCompletionResponse = await self._model.completion_async(
                    messages=messages_builder.build(),
                )  # type: ignore
                extension = response.content
                messages_builder.add_assistant_message(extension)
                claims += RECORD_DELIMITER + extension.strip().removesuffix(
                    COMPLETION_DELIMITER
                )

                # If this isn't the last loop, check to see if we should continue
                if i >= self._max_gleanings - 1:
                    break

                messages_builder.add_user_message(LOOP_PROMPT)
                response: LLMCompletionResponse = await self._model.completion_async(
                    messages=messages_builder.build(),
                )  # type: ignore

                if response.content != "Y":
                    break

        return self._parse_claim_tuples(results)

    def _parse_claim_tuples(self, claims: str) -> list[dict[str, Any]]:
        """Parse claim tuples."""

        def pull_field(index: int, fields: list[str]) -> str | None:
            return fields[index].strip() if len(fields) > index else None

        result: list[dict[str, Any]] = []
        claims_values = (
            claims.strip().removesuffix(COMPLETION_DELIMITER).split(RECORD_DELIMITER)
        )
        for claim in claims_values:
            claim = claim.strip().removeprefix("(").removesuffix(")")

            # Ignore the completion delimiter
            if claim == COMPLETION_DELIMITER:
                continue

            claim_fields = claim.split(TUPLE_DELIMITER)
            result.append({
                "subject_id": pull_field(0, claim_fields),
                "object_id": pull_field(1, claim_fields),
                "type": pull_field(2, claim_fields),
                "status": pull_field(3, claim_fields),
                "start_date": pull_field(4, claim_fields),
                "end_date": pull_field(5, claim_fields),
                "description": pull_field(6, claim_fields),
                "source_text": pull_field(7, claim_fields),
            })
        return result
