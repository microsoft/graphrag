# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Retry configuration."""

from pydantic import BaseModel, ConfigDict, Field

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
