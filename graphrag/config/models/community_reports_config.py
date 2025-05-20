# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.config.defaults import graphrag_config_defaults
from graphrag.config.models.language_model_config import LanguageModelConfig
from graphrag.config.prompt_getter import get_prompt_content


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
    endpoint_url: str | None = Field(
        description="The endpoint URL for the S3 API. Useful for S3-compatible storage like MinIO.",
        default=graphrag_config_defaults.community_reports.endpoint_url,
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
            "graph_prompt": get_prompt_content(self.graph_prompt, root_dir, self.endpoint_url),
            "text_prompt": get_prompt_content(self.text_prompt, root_dir, self.endpoint_url),
            "max_report_length": self.max_length,
            "max_input_length": self.max_input_length,
        }
