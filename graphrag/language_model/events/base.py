# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Base model events protocol."""

from typing import Any, Protocol


class ModelEventHandler(Protocol):
    """Protocol for Model event handling."""

    async def on_error(
        self,
        error: BaseException | None,
        traceback: str | None = None,
        arguments: dict[str, Any] | None = None,
    ) -> None:
        """Handle an model error."""
        ...
