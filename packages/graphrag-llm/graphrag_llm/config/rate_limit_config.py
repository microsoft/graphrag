# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""RateLimit configuration."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from graphrag_llm.config.types import RateLimitType


class RateLimitConfig(BaseModel):
    """Configuration for rate limit behavior."""

    model_config = ConfigDict(extra="allow")
    """Allow extra fields to support custom RateLimit implementations."""

    type: str = Field(
        default=RateLimitType.SlidingWindow,
        description="The type of rate limit strategy to use. [sliding_window] (default: sliding_window).",
    )

    period_in_seconds: int | None = Field(
        default=None,
        description="The period in seconds for the rate limit window. (default: 60).",
    )

    requests_per_period: int | None = Field(
        default=None,
        description="The maximum number of requests allowed per period. (default: None, no limit).",
    )

    tokens_per_period: int | None = Field(
        default=None,
        description="The maximum number of tokens allowed per period. (default: None, no limit).",
    )

    def _validate_sliding_window_config(self) -> None:
        """Validate Sliding Window rate limit configuration."""
        if self.period_in_seconds is not None and self.period_in_seconds <= 0:
            msg = "period_in_seconds must be a positive integer for Sliding Window rate limit."
            raise ValueError(msg)

        if not self.requests_per_period and not self.tokens_per_period:
            msg = "At least one of requests_per_period or tokens_per_period must be specified for Sliding Window rate limit."
            raise ValueError(msg)

        if self.requests_per_period is not None and self.requests_per_period <= 0:
            msg = "requests_per_period must be a positive integer for Sliding Window rate limit."
            raise ValueError(msg)

        if self.tokens_per_period is not None and self.tokens_per_period <= 0:
            msg = "tokens_per_period must be a positive integer for Sliding Window rate limit."
            raise ValueError(msg)

    @model_validator(mode="after")
    def _validate_model(self):
        """Validate the rate limit configuration based on its type."""
        if self.type == RateLimitType.SlidingWindow:
            self._validate_sliding_window_config()
        return self
