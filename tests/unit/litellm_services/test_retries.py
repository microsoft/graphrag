# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Test LiteLLM Retries."""

import time

import pytest

from graphrag.language_model.providers.litellm.services.retry.retry_factory import (
    RetryFactory,
)

retry_factory = RetryFactory()


@pytest.mark.parametrize(
    ("strategy", "max_attempts", "max_retry_wait", "expected_time"),
    [
        (
            "native",
            3,  # 3 retries
            0,  # native retry does not adhere to max_retry_wait
            0,  # immediate retry, expect 0 seconds elapsed time
        ),
        (
            "exponential_backoff",
            3,  # 3 retries
            0,  # exponential retry does not adhere to max_retry_wait
            14,  # (2^1 + jitter) + (2^2 + jitter) + (2^3 + jitter) = 2 + 4 + 8 + 3*jitter = 14 seconds min total runtime
        ),
        (
            "random_wait",
            3,  # 3 retries
            2,  # random wait [0, 2] seconds
            0,  # unpredictable, don't know what the total runtime will be
        ),
        (
            "incremental_wait",
            3,  # 3 retries
            3,  # wait for a max of 3 seconds on a single retry.
            6,  # Wait 3/3 * 1 on first retry, 3/3 * 2 on second, 3/3 * 3 on third, 1 + 2 + 3 = 6 seconds total runtime.
        ),
    ],
)
def test_retries(
    strategy: str, max_attempts: int, max_retry_wait: int, expected_time: float
) -> None:
    """
    Test various retry strategies with various configurations.

    Args
    ----
        strategy: The retry strategy to use.
        max_attempts: The maximum number of retry attempts.
        max_retry_wait: The maximum wait time between retries.
    """
    retry_service = retry_factory.create(
        strategy=strategy,
        max_attempts=max_attempts,
        max_retry_wait=max_retry_wait,
    )

    retries = 0

    def mock_func():
        nonlocal retries
        retries += 1
        msg = "Mock error for testing retries"
        raise ValueError(msg)

    start_time = time.time()
    with pytest.raises(ValueError, match="Mock error for testing retries"):
        retry_service.retry(func=mock_func)
    elapsed_time = time.time() - start_time

    # subtract 1 from retries because the first call is not a retry
    assert retries - 1 == max_attempts, (
        f"Expected {max_attempts} retries, got {retries}"
    )
    assert elapsed_time >= expected_time, (
        f"Expected elapsed time >= {expected_time}, got {elapsed_time}"
    )


@pytest.mark.parametrize(
    ("strategy", "max_attempts", "max_retry_wait", "expected_time"),
    [
        (
            "native",
            3,  # 3 retries
            0,  # native retry does not adhere to max_retry_wait
            0,  # immediate retry, expect 0 seconds elapsed time
        ),
        (
            "exponential_backoff",
            3,  # 3 retries
            0,  # exponential retry does not adhere to max_retry_wait
            14,  # (2^1 + jitter) + (2^2 + jitter) + (2^3 + jitter) = 2 + 4 + 8 + 3*jitter = 14 seconds min total runtime
        ),
        (
            "random_wait",
            3,  # 3 retries
            2,  # random wait [0, 2] seconds
            0,  # unpredictable, don't know what the total runtime will be
        ),
        (
            "incremental_wait",
            3,  # 3 retries
            3,  # wait for a max of 3 seconds on a single retry.
            6,  # Wait 3/3 * 1 on first retry, 3/3 * 2 on second, 3/3 * 3 on third, 1 + 2 + 3 = 6 seconds total runtime.
        ),
    ],
)
async def test_retries_async(
    strategy: str, max_attempts: int, max_retry_wait: int, expected_time: float
) -> None:
    """
    Test various retry strategies with various configurations.

    Args
    ----
        strategy: The retry strategy to use.
        max_attempts: The maximum number of retry attempts.
        max_retry_wait: The maximum wait time between retries.
    """
    retry_service = retry_factory.create(
        strategy=strategy,
        max_attempts=max_attempts,
        max_retry_wait=max_retry_wait,
    )

    retries = 0

    async def mock_func():  # noqa: RUF029
        nonlocal retries
        retries += 1
        msg = "Mock error for testing retries"
        raise ValueError(msg)

    start_time = time.time()
    with pytest.raises(ValueError, match="Mock error for testing retries"):
        await retry_service.aretry(func=mock_func)
    elapsed_time = time.time() - start_time

    # subtract 1 from retries because the first call is not a retry
    assert retries - 1 == max_attempts, (
        f"Expected {max_attempts} retries, got {retries}"
    )
    assert elapsed_time >= expected_time, (
        f"Expected elapsed time >= {expected_time}, got {elapsed_time}"
    )
