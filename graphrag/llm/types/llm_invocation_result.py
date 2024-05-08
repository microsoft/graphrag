# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Typing definitions for the OpenAI DataShaper package."""

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class LLMInvocationResult(Generic[T]):
    """The result of an LLM invocation."""

    result: T | None
    """The result of the LLM invocation."""

    name: str
    """The operation name of the result"""

    num_retries: int
    """The number of retries the invocation took."""

    total_time: float
    """The total time of the LLM invocation."""

    call_times: list[float]
    """The network times of individual invocations."""

    input_tokens: int
    """The number of input tokens."""

    output_tokens: int
    """The number of output tokens."""
