# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Test LiteLLM Rate Limiter."""

import threading
import time
from math import ceil
from queue import Queue

import pytest

from graphrag.language_model.providers.litellm.services.rate_limiter.rate_limiter import (
    RateLimiter,
)
from graphrag.language_model.providers.litellm.services.rate_limiter.rate_limiter_factory import (
    RateLimiterFactory,
)
from tests.unit.litellm_services.utils import (
    assert_max_num_values_per_period,
    assert_stagger,
    bin_time_intervals,
)

rate_limiter_factory = RateLimiterFactory()

_period_in_seconds = 1
_rpm = 4
_tpm = 75
_tokens_per_request = 25
_stagger = _period_in_seconds / _rpm
_num_requests = 10


def test_binning():
    """Test binning timings into 1-second intervals."""
    values = [0.1, 0.2, 0.3, 0.4, 1.1, 1.2, 1.3, 1.4, 5.1]
    binned_values = bin_time_intervals(values, 1)
    assert binned_values == [
        [0.1, 0.2, 0.3, 0.4],
        [1.1, 1.2, 1.3, 1.4],
        [],
        [],
        [],
        [5.1],
    ]


def test_rate_limiter_validation():
    """Test that the rate limiter can be created with valid parameters."""

    # Valid parameters
    rate_limiter = rate_limiter_factory.create(
        strategy="static", rpm=60, tpm=10000, period_in_seconds=60
    )
    assert rate_limiter is not None

    # Invalid strategy
    with pytest.raises(
        ValueError,
        match=r"Strategy 'invalid_strategy' is not registered.",
    ):
        rate_limiter_factory.create(strategy="invalid_strategy", rpm=60, tpm=10000)

    # Both rpm and tpm are None
    with pytest.raises(
        ValueError,
        match=r"Both TPM and RPM cannot be None \(disabled\), one or both must be set to a positive integer.",
    ):
        rate_limiter_factory.create(strategy="static")

    # Invalid rpm
    with pytest.raises(
        ValueError,
        match=r"RPM and TPM must be either None \(disabled\) or positive integers.",
    ):
        rate_limiter_factory.create(strategy="static", rpm=-10)

    # Invalid tpm
    with pytest.raises(
        ValueError,
        match=r"RPM and TPM must be either None \(disabled\) or positive integers.",
    ):
        rate_limiter_factory.create(strategy="static", tpm=-10)

    # Invalid period_in_seconds
    with pytest.raises(
        ValueError, match=r"Period in seconds must be a positive integer."
    ):
        rate_limiter_factory.create(strategy="static", rpm=10, period_in_seconds=-10)


def test_rpm():
    """Test that the rate limiter enforces RPM limits."""
    rate_limiter = rate_limiter_factory.create(
        strategy="static", rpm=_rpm, period_in_seconds=_period_in_seconds
    )

    time_values: list[float] = []
    start_time = time.time()
    for _ in range(_num_requests):
        with rate_limiter.acquire(token_count=_tokens_per_request):
            time_values.append(time.time() - start_time)

    assert len(time_values) == _num_requests
    binned_time_values = bin_time_intervals(time_values, _period_in_seconds)

    """
    With _num_requests = 10 and _rpm = 4, we expect the requests to be
    distributed across ceil(10/4) = 3 bins:
    with a stagger of 1/4 = 0.25 seconds between requests.
    """

    expected_num_bins = ceil(_num_requests / _rpm)
    assert len(binned_time_values) == expected_num_bins

    assert_max_num_values_per_period(binned_time_values, _rpm)
    assert_stagger(time_values, _stagger)


def test_tpm():
    """Test that the rate limiter enforces TPM limits."""
    rate_limiter = rate_limiter_factory.create(
        strategy="static", tpm=_tpm, period_in_seconds=_period_in_seconds
    )

    time_values: list[float] = []
    start_time = time.time()
    for _ in range(_num_requests):
        with rate_limiter.acquire(token_count=_tokens_per_request):
            time_values.append(time.time() - start_time)

    assert len(time_values) == _num_requests
    binned_time_values = bin_time_intervals(time_values, _period_in_seconds)

    """
    With _num_requests = 10, _tpm = 75 and _tokens_per_request = 25, we expect the requests to be
    distributed across ceil( (10 * 25) / 75) ) = 4 bins
    and max requests per bin = (75 / 25) = 3 requests per bin.
    """

    expected_num_bins = ceil((_num_requests * _tokens_per_request) / _tpm)
    assert len(binned_time_values) == expected_num_bins

    max_num_of_requests_per_bin = _tpm // _tokens_per_request
    assert_max_num_values_per_period(binned_time_values, max_num_of_requests_per_bin)


def test_token_in_request_exceeds_tpm():
    """Test that the rate limiter allows for requests that use more tokens than the TPM.

    A rate limiter could be configured with a tpm of 1000 but a request may use 2000 tokens,
    greater than the tpm limit but still below the context window limit of the underlying model.
    In this case, the request should still be allowed to proceed but may take up its own rate limit bin.
    """
    rate_limiter = rate_limiter_factory.create(
        strategy="static", tpm=_tpm, period_in_seconds=_period_in_seconds
    )

    time_values: list[float] = []
    start_time = time.time()
    for _ in range(2):
        with rate_limiter.acquire(token_count=_tpm * 2):
            time_values.append(time.time() - start_time)

    assert len(time_values) == 2
    binned_time_values = bin_time_intervals(time_values, _period_in_seconds)

    """
    Since each request exceeds the tpm, we expect each request to still be fired off but to be in its own bin
    """

    assert len(binned_time_values) == 2

    assert_max_num_values_per_period(binned_time_values, 1)


def test_rpm_and_tpm_with_rpm_as_limiting_factor():
    """Test that the rate limiter enforces RPM and TPM limits."""
    rate_limiter = rate_limiter_factory.create(
        strategy="static", rpm=_rpm, tpm=_tpm, period_in_seconds=_period_in_seconds
    )

    time_values: list[float] = []
    start_time = time.time()
    for _ in range(_num_requests):
        # Use 0 tokens per request to simulate RPM as the limiting factor
        with rate_limiter.acquire(token_count=0):
            time_values.append(time.time() - start_time)

    assert len(time_values) == _num_requests
    binned_time_values = bin_time_intervals(time_values, _period_in_seconds)

    """
    With _num_requests = 10 and _rpm = 4, we expect the requests to be
    distributed across ceil(10/4) = 3 bins:
    with a stagger of 1/4 = 0.25 seconds between requests.
    """

    expected_num_bins = ceil(_num_requests / _rpm)
    assert len(binned_time_values) == expected_num_bins

    assert_max_num_values_per_period(binned_time_values, _rpm)
    assert_stagger(time_values, _stagger)


def test_rpm_and_tpm_with_tpm_as_limiting_factor():
    """Test that the rate limiter enforces TPM limits."""
    rate_limiter = rate_limiter_factory.create(
        strategy="static", rpm=_rpm, tpm=_tpm, period_in_seconds=_period_in_seconds
    )

    time_values: list[float] = []
    start_time = time.time()
    for _ in range(_num_requests):
        with rate_limiter.acquire(token_count=_tokens_per_request):
            time_values.append(time.time() - start_time)

    assert len(time_values) == _num_requests
    binned_time_values = bin_time_intervals(time_values, _period_in_seconds)

    """
    With _num_requests = 10, _tpm = 75 and _tokens_per_request = 25, we expect the requests to be
    distributed across ceil( (10 * 25) / 75) ) = 4 bins
    and max requests per bin = (75 / 25) = 3 requests per bin.
    """

    expected_num_bins = ceil((_num_requests * _tokens_per_request) / _tpm)
    assert len(binned_time_values) == expected_num_bins

    max_num_of_requests_per_bin = _tpm // _tokens_per_request
    assert_max_num_values_per_period(binned_time_values, max_num_of_requests_per_bin)
    assert_stagger(time_values, _stagger)


def _run_rate_limiter(
    rate_limiter: RateLimiter,
    # Acquire cost
    input_queue: Queue[int | None],
    # time value
    output_queue: Queue[float | None],
):
    while True:
        token_count = input_queue.get()
        if token_count is None:
            break
        with rate_limiter.acquire(token_count=token_count):
            output_queue.put(time.time())


def test_rpm_threaded():
    """Test that the rate limiter enforces RPM limits in a threaded environment."""
    rate_limiter = rate_limiter_factory.create(
        strategy="static", rpm=_rpm, tpm=_tpm, period_in_seconds=_period_in_seconds
    )

    input_queue: Queue[int | None] = Queue()
    output_queue: Queue[float | None] = Queue()

    # Spin up threads for half the number of requests
    threads = [
        threading.Thread(
            target=_run_rate_limiter,
            args=(rate_limiter, input_queue, output_queue),
        )
        for _ in range(_num_requests // 2)  # Create 5 threads
    ]

    for thread in threads:
        thread.start()

    start_time = time.time()
    for _ in range(_num_requests):
        # Use 0 tokens per request to simulate RPM as the limiting factor
        input_queue.put(0)

    # Signal threads to stop
    for _ in range(len(threads)):
        input_queue.put(None)

    for thread in threads:
        thread.join()

    output_queue.put(None)  # Signal end of output

    time_values = []
    while True:
        time_value = output_queue.get()
        if time_value is None:
            break
        time_values.append(time_value - start_time)

    time_values.sort()

    assert len(time_values) == _num_requests
    binned_time_values = bin_time_intervals(time_values, _period_in_seconds)

    """
    With _num_requests = 10 and _rpm = 4, we expect the requests to be
    distributed across ceil(10/4) = 3 bins:
    with a stagger of 1/4 = 0.25 seconds between requests.
    """

    expected_num_bins = ceil(_num_requests / _rpm)
    assert len(binned_time_values) == expected_num_bins

    assert_max_num_values_per_period(binned_time_values, _rpm)
    assert_stagger(time_values, _stagger)


def test_tpm_threaded():
    """Test that the rate limiter enforces TPM limits in a threaded environment."""
    rate_limiter = rate_limiter_factory.create(
        strategy="static", rpm=_rpm, tpm=_tpm, period_in_seconds=_period_in_seconds
    )

    input_queue: Queue[int | None] = Queue()
    output_queue: Queue[float | None] = Queue()

    # Spin up threads for half the number of requests
    threads = [
        threading.Thread(
            target=_run_rate_limiter,
            args=(rate_limiter, input_queue, output_queue),
        )
        for _ in range(_num_requests // 2)  # Create 5 threads
    ]

    for thread in threads:
        thread.start()

    start_time = time.time()
    for _ in range(_num_requests):
        input_queue.put(_tokens_per_request)

    # Signal threads to stop
    for _ in range(len(threads)):
        input_queue.put(None)

    for thread in threads:
        thread.join()

    output_queue.put(None)  # Signal end of output

    time_values = []
    while True:
        time_value = output_queue.get()
        if time_value is None:
            break
        time_values.append(time_value - start_time)

    time_values.sort()

    assert len(time_values) == _num_requests
    binned_time_values = bin_time_intervals(time_values, _period_in_seconds)

    """
    With _num_requests = 10, _tpm = 75 and _tokens_per_request = 25, we expect the requests to be
    distributed across ceil( (10 * 25) / 75) ) = 4 bins
    and max requests per bin = (75 / 25) = 3 requests per bin.
    """

    expected_num_bins = ceil((_num_requests * _tokens_per_request) / _tpm)
    assert len(binned_time_values) == expected_num_bins

    max_num_of_requests_per_bin = _tpm // _tokens_per_request
    assert_max_num_values_per_period(binned_time_values, max_num_of_requests_per_bin)
    assert_stagger(time_values, _stagger)
