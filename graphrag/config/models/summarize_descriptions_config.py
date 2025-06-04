# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.config.defaults import graphrag_config_defaults
from graphrag.config.models.language_model_config import LanguageModelConfig
from graphrag.config.prompt_getter import get_prompt_content


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
    endpoint_url: str | None = Field(
        description="The endpoint URL for the S3 API. Useful for S3-compatible storage like MinIO.",
        default=graphrag_config_defaults.summarize_descriptions.endpoint_url,
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
            "summarize_prompt": get_prompt_content(self.prompt, root_dir, self.endpoint_url),
            "max_summary_length": self.max_length,
            "max_input_tokens": self.max_input_tokens,
        }
