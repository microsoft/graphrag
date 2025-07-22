# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""FNLLM llm events provider."""

from typing import Any

from fnllm.events import LLMEvents

from graphrag.index.typing.error_handler import ErrorHandlerFn


class FNLLMEvents(LLMEvents):
    """FNLLM events handler that calls the error handler."""

    def __init__(self, on_error: ErrorHandlerFn):
        self._on_error = on_error

    async def on_error(
        self,
        error: BaseException | None,
        traceback: str | None = None,
        arguments: dict[str, Any] | None = None,
    ) -> None:
        """Handle an fnllm error."""
        self._on_error(error, traceback, arguments)
