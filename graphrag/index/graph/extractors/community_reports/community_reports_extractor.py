# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'CommunityReportsResult' and 'CommunityReportsExtractor' models."""

import logging
import traceback
from dataclasses import dataclass
from typing import Any

from graphrag.index.typing import ErrorHandlerFn
from graphrag.index.utils import dict_has_keys_with_types
from graphrag.llm import CompletionLLM

from .prompts import COMMUNITY_REPORT_PROMPT

log = logging.getLogger(__name__)


@dataclass
class CommunityReportsResult:
    """Community reports result class definition."""

    output: str
    structured_output: dict


class CommunityReportsExtractor:
    """Community reports extractor class definition."""

    _llm: CompletionLLM
    _input_text_key: str
    _extraction_prompt: str
    _output_formatter_prompt: str
    _on_error: ErrorHandlerFn
    _max_report_length: int

    def __init__(
        self,
        llm_invoker: CompletionLLM,
        input_text_key: str | None = None,
        extraction_prompt: str | None = None,
        on_error: ErrorHandlerFn | None = None,
        max_report_length: int | None = None,
    ):
        """Init method definition."""
        self._llm = llm_invoker
        self._input_text_key = input_text_key or "input_text"
        self._extraction_prompt = extraction_prompt or COMMUNITY_REPORT_PROMPT
        self._on_error = on_error or (lambda _e, _s, _d: None)
        self._max_report_length = max_report_length or 1500

    async def __call__(self, inputs: dict[str, Any]):
        """Call method definition."""
        output = None
        try:
            response = (
                await self._llm(
                    self._extraction_prompt,
                    json=True,
                    name="create_community_report",
                    variables={self._input_text_key: inputs[self._input_text_key]},
                    is_response_valid=lambda x: dict_has_keys_with_types(
                        x,
                        [
                            ("title", str),
                            ("summary", str),
                            ("findings", list),
                            ("rating", float),
                            ("rating_explanation", str),
                        ],
                        inplace=True,
                    ),
                    model_parameters={"max_tokens": self._max_report_length},
                )
                or {}
            )
            output = response.json or {}
        except Exception as e:
            log.exception("error generating community report")
            self._on_error(e, traceback.format_exc(), None)
            output = {}

        text_output = self._get_text_output(output)
        return CommunityReportsResult(
            structured_output=output,
            output=text_output,
        )

    def _get_text_output(self, parsed_output: dict) -> str:
        title = parsed_output.get("title", "Report")
        summary = parsed_output.get("summary", "")
        findings = parsed_output.get("findings", [])

        def finding_summary(finding: dict):
            if isinstance(finding, str):
                return finding
            return finding.get("summary")

        def finding_explanation(finding: dict):
            if isinstance(finding, str):
                return ""
            return finding.get("explanation")

        report_sections = "\n\n".join(
            f"## {finding_summary(f)}\n\n{finding_explanation(f)}" for f in findings
        )
        return f"# {title}\n\n{summary}\n\n{report_sections}"
