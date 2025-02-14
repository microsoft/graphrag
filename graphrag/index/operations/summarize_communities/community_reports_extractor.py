# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'CommunityReportsResult' and 'CommunityReportsExtractor' models."""

import json
import logging
import traceback
from dataclasses import dataclass
from typing import Any

from fnllm.types import ChatLLM
from pydantic import BaseModel, Field

from graphrag.index.typing import ErrorHandlerFn
from graphrag.prompts.index.community_report import COMMUNITY_REPORT_PROMPT

log = logging.getLogger(__name__)


class FindingModel(BaseModel):
    """A model for the expected LLM response shape."""

    summary: str = Field(description="The summary of the finding.")
    explanation: str = Field(description="An explanation of the finding.")


class CommunityReportResponse(BaseModel):
    """A model for the expected LLM response shape."""

    title: str = Field(description="The title of the report.")
    summary: str = Field(description="A summary of the report.")
    findings: list[FindingModel] = Field(
        description="A list of findings in the report."
    )
    rating: float = Field(description="The rating of the report.")
    rating_explanation: str = Field(description="An explanation of the rating.")


@dataclass
class CommunityReportsResult:
    """Community reports result class definition."""

    output: str
    structured_output: CommunityReportResponse | None


class CommunityReportsExtractor:
    """Community reports extractor class definition."""

    _llm: ChatLLM
    _input_text_key: str
    _extraction_prompt: str
    _output_formatter_prompt: str
    _on_error: ErrorHandlerFn
    _max_report_length: int

    def __init__(
        self,
        llm_invoker: ChatLLM,
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
            input_text = inputs[self._input_text_key]
            prompt = self._extraction_prompt.replace(
                "{" + self._input_text_key + "}", input_text
            )
            response = await self._llm(
                prompt,
                json=True,  # Leaving this as True to avoid creating new cache entries
                name="create_community_report",
                json_model=CommunityReportResponse,  # A model is required when using json mode
                model_parameters={"max_tokens": self._max_report_length},
            )

            # TODO: Json mode is currently broken on fnllm: https://github.com/microsoft/essex-toolkit/issues/364
            # once fixed, just assign to output the response.parsed_json
            output = CommunityReportResponse.model_validate(
                json.loads(response.output.content)
            )
        except Exception as e:
            log.exception("error generating community report")
            self._on_error(e, traceback.format_exc(), None)

        text_output = self._get_text_output(output) if output else ""
        return CommunityReportsResult(
            structured_output=output,
            output=text_output,
        )

    def _get_text_output(self, report: CommunityReportResponse) -> str:
        report_sections = "\n\n".join(
            f"## {f.summary}\n\n{f.explanation}" for f in report.findings
        )
        return f"# {report.title}\n\n{report.summary}\n\n{report_sections}"
