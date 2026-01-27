# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field

from graphrag.config.defaults import graphrag_config_defaults
from graphrag.prompts.index.summarize_descriptions import SUMMARIZE_PROMPT


@dataclass
class SummarizeDescriptionsPrompts:
    """Description summarization prompt templates."""

    summarize_prompt: str


class SummarizeDescriptionsConfig(BaseModel):
    """Configuration section for description summarization."""

    completion_model_id: str = Field(
        description="The model ID to use for summarization.",
        default=graphrag_config_defaults.summarize_descriptions.completion_model_id,
    )
    model_instance_name: str = Field(
        description="The model singleton instance name. This primarily affects the cache storage partitioning.",
        default=graphrag_config_defaults.summarize_descriptions.model_instance_name,
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

    def resolved_prompts(self) -> SummarizeDescriptionsPrompts:
        """Get the resolved description summarization prompts."""
        return SummarizeDescriptionsPrompts(
            summarize_prompt=Path(self.prompt).read_text(encoding="utf-8")
            if self.prompt
            else SUMMARIZE_PROMPT,
        )
