# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pathlib import Path

from pydantic import BaseModel, Field

from graphrag.config.defaults import graphrag_config_defaults
from graphrag.prompts.index.summarize_descriptions import SUMMARIZE_PROMPT


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

    def resolved_prompts(self, root_dir: str) -> dict:
        """Get the resolved description summarization prompts."""
        return {
            "summarize_prompt": (Path(root_dir) / self.prompt).read_text(
                encoding="utf-8"
            )
            if self.prompt
            else SUMMARIZE_PROMPT,
        }
