# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pathlib import Path

from pydantic import BaseModel, Field

from graphrag.config.defaults import graphrag_config_defaults
from graphrag.config.models.language_model_config import LanguageModelConfig


class SummarizeDescriptionsConfig(BaseModel):
    """Configuration section for description summarization."""

    model_id: str = Field(
        description="The model ID to use for summarization.",
        default=graphrag_config_defaults.summarize_descriptions.model_id,
    )
    prompt: str | None = Field(
        description="The description summarization prompt to use.",
        default=graphrag_config_defaults.summarize_descriptions.prompt,
    )
    max_length: int = Field(
        description="The description summarization maximum length.",
        default=graphrag_config_defaults.summarize_descriptions.max_length,
    )
    max_input_tokens: int = Field(
        description="Maximum tokens to submit from the input entity descriptions.",
        default=graphrag_config_defaults.summarize_descriptions.max_input_tokens,
    )
    strategy: dict | None = Field(
        description="The override strategy to use.",
        default=graphrag_config_defaults.summarize_descriptions.strategy,
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
            "summarize_prompt": (Path(root_dir) / self.prompt).read_text(
                encoding="utf-8"
            )
            if self.prompt
            else None,
            "max_summary_length": self.max_length,
            "max_input_tokens": self.max_input_tokens,
        }
