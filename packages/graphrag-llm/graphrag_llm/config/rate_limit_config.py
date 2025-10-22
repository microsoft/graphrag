# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""RateLimit configuration."""

from pydantic import BaseModel, ConfigDict, Field

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
