# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'CommunityReportsResult' and 'CommunityReportsExtractor' models."""

import logging
import traceback
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from graphrag.index.typing.error_handler import ErrorHandlerFn

if TYPE_CHECKING:
    from graphrag_llm.completion import LLMCompletion

logger = logging.getLogger(__name__)

# these tokens are used in the prompt
INPUT_TEXT_KEY = "input_text"
MAX_LENGTH_KEY = "max_report_length"


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


def _is_unsupported_response_format_error(e: Exception) -> bool:
    """Check if the error is due to unsupported response_format."""
    msg = str(e).lower()
    return any(
        phrase in msg
        for phrase in [
            "response_format",
            "json_schema",
            "unsupported",
            "unavailable",
        ]
    )


def _parse_json_from_text(
    text: str, model: type[CommunityReportResponse]
) -> CommunityReportResponse:
    """Extract and parse JSON from LLM text output."""
    text = text or ""
    # Try code block first
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if not m:
        m = re.search(r"(\{.*\})", text, re.DOTALL)
    json_text = m.group(1).strip() if m else text.strip()
    data = json.loads(json_text)
    return model(**data)


class CommunityReportsExtractor:
    def __init__(
        self,
        model: "LLMCompletion",
        extraction_prompt: str,
        max_report_length: int,
        on_error: ErrorHandlerFn | None = None,
    ):
        self._model = model
        self._extraction_prompt = extraction_prompt
        self._on_error = on_error or (lambda _e, _s, _d: None)
        self._max_report_length = max_report_length

    async def __call__(self, input_text: str):
        output = None
        try:
            prompt = self._extraction_prompt.format(**{
                INPUT_TEXT_KEY: input_text,
                MAX_LENGTH_KEY: str(self._max_report_length),
            })

            # Strategy 1: Try structured output with Pydantic model (json_schema)
            try:
                response = await self._model.completion_async(
                    messages=prompt,
                    response_format=CommunityReportResponse,
                )
                output = response.formatted_response
            except Exception as schema_error:
                if not _is_unsupported_response_format_error(schema_error):
                    raise

                logger.warning(
                    "json_schema not supported by provider, "
                    "falling back to json_object mode"
                )

                # Strategy 2: Fallback to json_object
                try:
                    response = await self._model.completion_async(
                        messages=prompt,
                        response_format={"type": "json_object"},
                    )
                    output = _parse_json_from_text(
                        response.content, CommunityReportResponse
                    )
                except Exception as json_error:
                    if not _is_unsupported_response_format_error(json_error):
                        raise

                    logger.warning(
                        "json_object not supported by provider, "
                        "falling back to plain text parsing"
                    )

                    # Strategy 3: Final fallback to plain text
                    response = await self._model.completion_async(
                        messages=prompt,
                    )
                    output = _parse_json_from_text(
                        response.content, CommunityReportResponse
                    )

        except Exception as e:
            logger.exception("error generating community report")
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
