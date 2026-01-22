# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Tokenizer model configuration."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

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

    def _validate_litellm_config(self) -> None:
        """Validate LiteLLM tokenizer configuration."""
        if self.model_id is None or self.model_id.strip() == "":
            msg = "model_id must be specified for LiteLLM tokenizer."
            raise ValueError(msg)

    def _validate_tiktoken_config(self) -> None:
        """Validate TikToken tokenizer configuration."""
        if self.encoding_name is None or self.encoding_name.strip() == "":
            msg = "encoding_name must be specified for TikToken tokenizer."
            raise ValueError(msg)

    @model_validator(mode="after")
    def _validate_model(self):
        """Validate the tokenizer configuration based on its type."""
        if self.type == TokenizerType.LiteLLM:
            self._validate_litellm_config()
        elif self.type == TokenizerType.Tiktoken:
            self._validate_tiktoken_config()
        return self
