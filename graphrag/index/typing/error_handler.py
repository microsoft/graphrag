# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Shared error handler types."""

from collections.abc import Callable

ErrorHandlerFn = Callable[[BaseException | None, str | None, dict | None], None]
