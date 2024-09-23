# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Typing definitions for the OpenAI DataShaper package."""

from collections.abc import Callable

from .llm_invocation_result import LLMInvocationResult

ErrorHandlerFn = Callable[[BaseException | None, str | None, dict | None], None]
"""Error handler function type definition."""

LLMInvocationFn = Callable[[LLMInvocationResult], None]
"""Handler for LLM invocation results"""

OnCacheActionFn = Callable[[str, str | None], None]
"""Handler for cache hits"""

IsResponseValidFn = Callable[[dict], bool]
"""A function that checks if an LLM response is valid."""
