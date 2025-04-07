# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'ClaimExtractorResult' and 'ClaimExtractor' models."""

import logging
import traceback
from dataclasses import dataclass
from typing import Any

from graphrag.config.defaults import graphrag_config_defaults
from graphrag.index.typing.error_handler import ErrorHandlerFn
from graphrag.language_model.protocol.base import ChatModel
from graphrag.prompts.index.extract_claims import (
    CONTINUE_PROMPT,
    EXTRACT_CLAIMS_PROMPT,
    LOOP_PROMPT,
)

DEFAULT_TUPLE_DELIMITER = "<|>"
DEFAULT_RECORD_DELIMITER = "##"
DEFAULT_COMPLETION_DELIMITER = "<|COMPLETE|>"
log = logging.getLogger(__name__)


@dataclass
class ClaimExtractorResult:
    """Claim extractor result class definition."""

    output: list[dict]
    source_docs: dict[str, Any]


class ClaimExtractor:
    """Claim extractor class definition."""

    _model: ChatModel
    _extraction_prompt: str
    _summary_prompt: str
    _output_formatter_prompt: str
    _input_text_key: str
    _input_entity_spec_key: str
    _input_claim_description_key: str
    _tuple_delimiter_key: str
    _record_delimiter_key: str
    _completion_delimiter_key: str
    _max_gleanings: int
    _on_error: ErrorHandlerFn

    def __init__(
        self,
        model_invoker: ChatModel,
        extraction_prompt: str | None = None,
        input_text_key: str | None = None,
        input_entity_spec_key: str | None = None,
        input_claim_description_key: str | None = None,
        input_resolved_entities_key: str | None = None,
        tuple_delimiter_key: str | None = None,
        record_delimiter_key: str | None = None,
        completion_delimiter_key: str | None = None,
        max_gleanings: int | None = None,
        on_error: ErrorHandlerFn | None = None,
    ):
        """Init method definition."""
        self._model = model_invoker
        self._extraction_prompt = extraction_prompt or EXTRACT_CLAIMS_PROMPT
        self._input_text_key = input_text_key or "input_text"
        self._input_entity_spec_key = input_entity_spec_key or "entity_specs"
        self._tuple_delimiter_key = tuple_delimiter_key or "tuple_delimiter"
        self._record_delimiter_key = record_delimiter_key or "record_delimiter"
        self._completion_delimiter_key = (
            completion_delimiter_key or "completion_delimiter"
        )
        self._input_claim_description_key = (
            input_claim_description_key or "claim_description"
        )
        self._input_resolved_entities_key = (
            input_resolved_entities_key or "resolved_entities"
        )
        self._max_gleanings = (
            max_gleanings
            if max_gleanings is not None
            else graphrag_config_defaults.extract_claims.max_gleanings
        )
        self._on_error = on_error or (lambda _e, _s, _d: None)

    async def __call__(
        self, inputs: dict[str, Any], prompt_variables: dict | None = None
    ) -> ClaimExtractorResult:
        """Call method definition."""
        if prompt_variables is None:
            prompt_variables = {}
        texts = inputs[self._input_text_key]
        entity_spec = str(inputs[self._input_entity_spec_key])
        claim_description = inputs[self._input_claim_description_key]
        resolved_entities = inputs.get(self._input_resolved_entities_key, {})
        source_doc_map = {}

        prompt_args = {
            self._input_entity_spec_key: entity_spec,
            self._input_claim_description_key: claim_description,
            self._tuple_delimiter_key: prompt_variables.get(self._tuple_delimiter_key)
            or DEFAULT_TUPLE_DELIMITER,
            self._record_delimiter_key: prompt_variables.get(self._record_delimiter_key)
            or DEFAULT_RECORD_DELIMITER,
            self._completion_delimiter_key: prompt_variables.get(
                self._completion_delimiter_key
            )
            or DEFAULT_COMPLETION_DELIMITER,
        }

        all_claims: list[dict] = []
        for doc_index, text in enumerate(texts):
            document_id = f"d{doc_index}"
            try:
                claims = await self._process_document(prompt_args, text, doc_index)
                all_claims += [
                    self._clean_claim(c, document_id, resolved_entities) for c in claims
                ]
                source_doc_map[document_id] = text
            except Exception as e:
                log.exception("error extracting claim")
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
        self, prompt_args: dict, doc, doc_index: int
    ) -> list[dict]:
        record_delimiter = prompt_args.get(
            self._record_delimiter_key, DEFAULT_RECORD_DELIMITER
        )
        completion_delimiter = prompt_args.get(
            self._completion_delimiter_key, DEFAULT_COMPLETION_DELIMITER
        )

        response = await self._model.achat(
            self._extraction_prompt.format(**{
                self._input_text_key: doc,
                **prompt_args,
            })
        )
        results = response.output.content or ""
        claims = results.strip().removesuffix(completion_delimiter)

        # if gleanings are specified, enter a loop to extract more claims
        # there are two exit criteria: (a) we hit the configured max, (b) the model says there are no more claims
        if self._max_gleanings > 0:
            for i in range(self._max_gleanings):
                response = await self._model.achat(
                    CONTINUE_PROMPT,
                    name=f"extract-continuation-{i}",
                    history=response.history,
                )
                extension = response.output.content or ""
                claims += record_delimiter + extension.strip().removesuffix(
                    completion_delimiter
                )

                # If this isn't the last loop, check to see if we should continue
                if i >= self._max_gleanings - 1:
                    break

                response = await self._model.achat(
                    LOOP_PROMPT,
                    name=f"extract-loopcheck-{i}",
                    history=response.history,
                )

                if response.output.content != "Y":
                    break

        return self._parse_claim_tuples(results, prompt_args)

    def _parse_claim_tuples(
        self, claims: str, prompt_variables: dict
    ) -> list[dict[str, Any]]:
        """Parse claim tuples."""
        record_delimiter = prompt_variables.get(
            self._record_delimiter_key, DEFAULT_RECORD_DELIMITER
        )
        completion_delimiter = prompt_variables.get(
            self._completion_delimiter_key, DEFAULT_COMPLETION_DELIMITER
        )
        tuple_delimiter = prompt_variables.get(
            self._tuple_delimiter_key, DEFAULT_TUPLE_DELIMITER
        )

        def pull_field(index: int, fields: list[str]) -> str | None:
            return fields[index].strip() if len(fields) > index else None

        result: list[dict[str, Any]] = []
        claims_values = (
            claims.strip().removesuffix(completion_delimiter).split(record_delimiter)
        )
        for claim in claims_values:
            claim = claim.strip().removeprefix("(").removesuffix(")")

            # Ignore the completion delimiter
            if claim == completion_delimiter:
                continue

            claim_fields = claim.split(tuple_delimiter)
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
