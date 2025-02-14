# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pathlib import Path

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs
from graphrag.config.models.language_model_config import LanguageModelConfig


class CommunityReportsConfig(BaseModel):
    """Configuration section for community reports."""

    graph_prompt: str | None = Field(
        description="The community report extraction prompt to use for graph-based summarization.",
        default=None,
    )
    text_prompt: str | None = Field(
        description="The community report extraction prompt to use for text-based summarization.",
        default=None,
    )
    max_length: int = Field(
        description="The community report maximum length in tokens.",
        default=defs.COMMUNITY_REPORT_MAX_LENGTH,
    )
    max_input_length: int = Field(
        description="The maximum input length in tokens to use when generating reports.",
        default=defs.COMMUNITY_REPORT_MAX_INPUT_LENGTH,
    )
    strategy: dict | None = Field(
        description="The override strategy to use.", default=None
    )
    model_id: str = Field(
        description="The model ID to use for community reports.",
        default=defs.COMMUNITY_REPORT_MODEL_ID,
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
            "num_threads": model_config.concurrent_requests,
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
