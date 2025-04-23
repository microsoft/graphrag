# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pathlib import Path

from pydantic import BaseModel, Field

from graphrag.config.defaults import graphrag_config_defaults
from graphrag.config.models.language_model_config import LanguageModelConfig


class CommunityReportsConfig(BaseModel):
    """Configuration section for community reports."""

    model_id: str = Field(
        description="The model ID to use for community reports.",
        default=graphrag_config_defaults.community_reports.model_id,
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
    strategy: dict | None = Field(
        description="The override strategy to use.",
        default=graphrag_config_defaults.community_reports.strategy,
    )

    def resolved_strategy(
        self, root_dir: str, model_config: LanguageModelConfig
    ) -> dict:
        """Get the resolved community report extraction strategy."""
        from graphrag.index.operations.summarize_communities.typing import (
            CreateCommunityReportsStrategyType,
        )

        return self.strategy or {
            "type": CreateCommunityReportsStrategyType.graph_intelligence,
            "llm": model_config.model_dump(),
            "graph_prompt": (Path(root_dir) / self.graph_prompt).read_text(
                encoding="utf-8"
            )
            if self.graph_prompt
            else None,
            "text_prompt": (Path(root_dir) / self.text_prompt).read_text(
                encoding="utf-8"
            )
            if self.text_prompt
            else None,
            "max_report_length": self.max_length,
            "max_input_length": self.max_input_length,
        }
