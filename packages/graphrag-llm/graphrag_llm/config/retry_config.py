# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Retry configuration."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from graphrag_llm.config.types import RetryType


class RetryConfig(BaseModel):
    """Configuration for retry behavior."""

    model_config = ConfigDict(extra="allow")
    """Allow extra fields to support custom Retry implementations."""

    type: str = Field(
        default=RetryType.ExponentialBackoff,
        description="The type of retry strategy to use. [exponential_backoff, immediate] (default: exponential_backoff).",
    )

    max_retries: int | None = Field(
        default=None,
        description="The maximum number of retry attempts.",
    )

    base_delay: float | None = Field(
        default=None,
        description="The base delay in seconds for exponential backoff.",
    )

    jitter: bool | None = Field(
        default=None,
        description="Whether to apply jitter to the delay intervals in exponential backoff.",
    )

    max_delay: float | None = Field(
        default=None,
        description="The maximum delay in seconds between retries.",
    )

    def _validate_exponential_backoff_config(self) -> None:
        """Validate Exponential Backoff retry configuration."""
        if self.max_retries is not None and self.max_retries <= 1:
            msg = "max_retries must be greater than 1 for Exponential Backoff retry."
            raise ValueError(msg)

        if self.base_delay is not None and self.base_delay <= 1.0:
            msg = "base_delay must be greater than 1.0 for Exponential Backoff retry."
            raise ValueError(msg)

        if self.max_delay is not None and self.max_delay <= 1:
            msg = "max_delay must be greater than 1 for Exponential Backoff retry."
            raise ValueError(msg)

    def _validate_immediate_config(self) -> None:
        """Validate Immediate retry configuration."""
        if self.max_retries is not None and self.max_retries <= 1:
            msg = "max_retries must be greater than 1 for Immediate retry."
            raise ValueError(msg)

    @model_validator(mode="after")
    def _validate_model(self):
        """Validate the retry configuration based on its type."""
        if self.type == RetryType.ExponentialBackoff:
            self._validate_exponential_backoff_config()
        elif self.type == RetryType.Immediate:
            self._validate_immediate_config()
        return self
