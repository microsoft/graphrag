# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from pathlib import Path

from pydantic import Field

from graphrag.index.default_config.parameters.defaults import (
    DEFAULT_SUMMARIZE_DESCRIPTIONS_MAX_LENGTH,
)
from graphrag.index.verbs.entities.summarize import SummarizeStrategyType

from .llm_config_model import LLMConfigModel


class SummarizeDescriptionsConfigModel(LLMConfigModel):
    """Configuration section for description summarization."""

    prompt: str | None = Field(
        description="The description summarization prompt to use.", default=None
    )
    max_length: int = Field(
        description="The description summarization maximum length.",
        default=DEFAULT_SUMMARIZE_DESCRIPTIONS_MAX_LENGTH,
    )
    strategy: dict | None = Field(
        description="The override strategy to use.", default=None
    )

    def resolved_strategy(self, root_dir: str) -> dict:
        """Get the resolved description summarization strategy."""
        return self.strategy or {
            "type": SummarizeStrategyType.graph_intelligence,
            "llm": self.llm.model_dump(),
            **self.parallelization.model_dump(),
            "summarize_prompt": (Path(root_dir) / self.prompt).read_text()
            if self.prompt
            else None,
            "max_summary_length": self.max_length,
        }
