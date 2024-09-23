# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Create limiters for OpenAI API requests."""

import logging

from aiolimiter import AsyncLimiter

from graphrag.llm.types import LLMConfig

from .llm_limiter import LLMLimiter
from .tpm_rpm_limiter import TpmRpmLLMLimiter

log = logging.getLogger(__name__)

"""The global TPM limiters."""


def create_tpm_rpm_limiters(
    configuration: LLMConfig,
) -> LLMLimiter:
    """Get the limiters for a given model name."""
    tpm = configuration.tokens_per_minute
    rpm = configuration.requests_per_minute
    return TpmRpmLLMLimiter(
        None if tpm == 0 else AsyncLimiter(tpm or 50_000),
        None if rpm == 0 else AsyncLimiter(rpm or 10_000),
    )
