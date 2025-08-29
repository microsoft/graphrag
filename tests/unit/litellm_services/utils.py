# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""LiteLLM Test Utilities."""


def bin_time_intervals(
    time_values: list[float], time_interval: int
) -> list[list[float]]:
    """Bin values."""
    bins: list[list[float]] = []

    bin_number = 0
    for time_value in time_values:
        upper_bound = (bin_number * time_interval) + time_interval
        while time_value >= upper_bound:
            bin_number += 1
            upper_bound = (bin_number * time_interval) + time_interval
        while len(bins) <= bin_number:
            bins.append([])
        bins[bin_number].append(time_value)

    return bins


def assert_max_num_values_per_period(
    periods: list[list[float]], max_values_per_period: int
):
    """Assert the number of values per period."""
    for period in periods:
        assert len(period) <= max_values_per_period


def assert_stagger(time_values: list[float], stagger: float):
    """Assert stagger."""
    for i in range(1, len(time_values)):
        assert time_values[i] - time_values[i - 1] >= stagger
