# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Test retry configuration loading."""

import pytest
from graphrag_llm.config import RetryConfig, RetryType


def test_exponential_backoff_validation() -> None:
    """Test that missing required parameters raise validation errors."""

    with pytest.raises(
        ValueError,
        match="max_retries must be greater than 1 for Exponential Backoff retry\\.",
    ):
        _ = RetryConfig(
            type=RetryType.ExponentialBackoff,
            max_retries=0,
        )

    with pytest.raises(
        ValueError,
        match="base_delay must be greater than 1\\.0 for Exponential Backoff retry\\.",
    ):
        _ = RetryConfig(
            type=RetryType.ExponentialBackoff,
            base_delay=0.5,
        )

    with pytest.raises(
        ValueError,
        match="max_delay must be greater than 1 for Exponential Backoff retry\\.",
    ):
        _ = RetryConfig(
            type=RetryType.ExponentialBackoff,
            max_delay=0.5,
        )

    # passes validation
    _ = RetryConfig(type=RetryType.ExponentialBackoff)
    _ = RetryConfig(
        type=RetryType.ExponentialBackoff,
        max_retries=5,
        base_delay=2.0,
        max_delay=30,
    )


def test_immediate_validation() -> None:
    """Test that missing required parameters raise validation errors."""

    with pytest.raises(
        ValueError,
        match="max_retries must be greater than 1 for Immediate retry\\.",
    ):
        _ = RetryConfig(
            type=RetryType.Immediate,
            max_retries=0,
        )

    # passes validation
    _ = RetryConfig(type=RetryType.Immediate)
    _ = RetryConfig(
        type=RetryType.Immediate,
        max_retries=3,
    )
