# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pathlib import Path

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs
from graphrag.config.models.language_model_config import LanguageModelConfig


class SummarizeDescriptionsConfig(BaseModel):
    """Configuration section for description summarization."""

    prompt: str | None = Field(
        description="The description summarization prompt to use.", default=None
    )
    max_length: int = Field(
        description="The description summarization maximum length.",
        default=defs.SUMMARIZE_DESCRIPTIONS_MAX_LENGTH,
    )
    strategy: dict | None = Field(
        description="The override strategy to use.", default=None
    )
    model_id: str = Field(
        description="The model ID to use for summarization.",
        default=defs.SUMMARIZE_MODEL_ID,
    )

    def resolved_strategy(
        self, root_dir: str, model_config: LanguageModelConfig
    ) -> dict:
        """Get the resolved description summarization strategy."""
        from graphrag.index.operations.summarize_descriptions import (
            SummarizeStrategyType,
        )

        return self.strategy or {
            "type": SummarizeStrategyType.graph_intelligence,
            "llm": model_config.model_dump(),
            "stagger": model_config.parallelization_stagger,
            "num_threads": model_config.parallelization_num_threads,
            "summarize_prompt": (Path(root_dir) / self.prompt).read_text(
                encoding="utf-8"
            )
            if self.prompt
            else None,
            "max_summary_length": self.max_length,
        }
