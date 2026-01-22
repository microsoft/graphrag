# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Test rate limit configuration loading."""

import pytest
from graphrag_llm.config import RateLimitConfig, RateLimitType


def test_sliding_window_validation() -> None:
    """Test that missing required parameters raise validation errors."""

    with pytest.raises(
        ValueError,
        match="period_in_seconds must be a positive integer for Sliding Window rate limit\\.",
    ):
        _ = RateLimitConfig(
            type=RateLimitType.SlidingWindow,
            period_in_seconds=0,
            requests_per_period=100,
            tokens_per_period=1000,
        )

    with pytest.raises(
        ValueError,
        match="At least one of requests_per_period or tokens_per_period must be specified for Sliding Window rate limit\\.",
    ):
        _ = RateLimitConfig(
            type=RateLimitType.SlidingWindow,
        )

    with pytest.raises(
        ValueError,
        match="requests_per_period must be a positive integer for Sliding Window rate limit\\.",
    ):
        _ = RateLimitConfig(
            type=RateLimitType.SlidingWindow,
            period_in_seconds=60,
            requests_per_period=-10,
        )

    with pytest.raises(
        ValueError,
        match="tokens_per_period must be a positive integer for Sliding Window rate limit\\.",
    ):
        _ = RateLimitConfig(
            type=RateLimitType.SlidingWindow,
            period_in_seconds=60,
            tokens_per_period=-10,
        )

    # passes validation
    _ = RateLimitConfig(
        type=RateLimitType.SlidingWindow,
        requests_per_period=100,
    )
    _ = RateLimitConfig(
        type=RateLimitType.SlidingWindow,
        tokens_per_period=1000,
    )
    _ = RateLimitConfig(
        type=RateLimitType.SlidingWindow,
        period_in_seconds=60,
        requests_per_period=100,
        tokens_per_period=1000,
    )
