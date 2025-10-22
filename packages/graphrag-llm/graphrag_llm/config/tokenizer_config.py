# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Tokenizer model configuration."""

from pydantic import BaseModel, ConfigDict, Field

from graphrag_llm.config.types import TokenizerType


class TokenizerConfig(BaseModel):
    """Configuration for a tokenizer."""

    model_config = ConfigDict(extra="allow")
    """Allow extra fields to support custom LLM provider implementations."""

    type: str = Field(
        default=TokenizerType.LiteLLM,
        description="The type of tokenizer to use. [litellm] (default: litellm).",
    )

    model_id: str | None = Field(
        default=None,
        description="The identifier for the tokenizer model. Example: openai/gpt-4o. Used by the litellm tokenizer.",
    )

    encoding_name: str | None = Field(
        default=None,
        description="The encoding name for the tokenizer. Example: gpt-4o.",
    )
