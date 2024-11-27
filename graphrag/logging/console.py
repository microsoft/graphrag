# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Console Reporter."""

from typing import Any

from graphrag.logging.base import StatusLogger


class ConsoleReporter(StatusLogger):
    """A reporter that writes to a console."""

    def error(self, message: str, details: dict[str, Any] | None = None):
        """Report an error."""
        print(message, details)  # noqa T201

    def warning(self, message: str, details: dict[str, Any] | None = None):
        """Report a warning."""
        _print_warning(message)

    def log(self, message: str, details: dict[str, Any] | None = None):
        """Report a log."""
        print(message, details)  # noqa T201


def _print_warning(skk):
    print(f"\033[93m {skk}\033[00m")  # noqa T201
