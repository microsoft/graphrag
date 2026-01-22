# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field

from graphrag.config.defaults import graphrag_config_defaults
from graphrag.prompts.index.community_report import COMMUNITY_REPORT_PROMPT
from graphrag.prompts.index.community_report_text_units import (
    COMMUNITY_REPORT_TEXT_PROMPT,
)


@dataclass
class CommunityReportPrompts:
    """Community report prompt templates."""

    graph_prompt: str
    text_prompt: str


class CommunityReportsConfig(BaseModel):
    """Configuration section for community reports."""

    completion_model_id: str = Field(
        description="The model ID to use for community reports.",
        default=graphrag_config_defaults.community_reports.completion_model_id,
    )
    model_instance_name: str = Field(
        description="The model singleton instance name. This primarily affects the cache storage partitioning.",
        default=graphrag_config_defaults.community_reports.model_instance_name,
    )
    graph_prompt: str | None = Field(
        description="The community report extraction prompt to use for graph-based summarization.",
        default=graphrag_config_defaults.community_reports.graph_prompt,
    )
    text_prompt: str | None = Field(
        description="The community report extraction prompt to use for text-based summarization.",
        default=graphrag_config_defaults.community_reports.text_prompt,
    )
    max_length: int = Field(
        description="The community report maximum length in tokens.",
        default=graphrag_config_defaults.community_reports.max_length,
    )
    max_input_length: int = Field(
        description="The maximum input length in tokens to use when generating reports.",
        default=graphrag_config_defaults.community_reports.max_input_length,
    )

    def resolved_prompts(self) -> CommunityReportPrompts:
        """Get the resolved community report extraction prompts."""
        return CommunityReportPrompts(
            graph_prompt=Path(self.graph_prompt).read_text(encoding="utf-8")
            if self.graph_prompt
            else COMMUNITY_REPORT_PROMPT,
            text_prompt=Path(self.text_prompt).read_text(encoding="utf-8")
            if self.text_prompt
            else COMMUNITY_REPORT_TEXT_PROMPT,
        )
