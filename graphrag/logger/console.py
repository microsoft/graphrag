# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Console Log."""

from typing import Any

from graphrag.logger.base import StatusLogger


class ConsoleReporter(StatusLogger):
    """A logger that writes to a console."""

    def error(self, message: str, details: dict[str, Any] | None = None):
        """Log an error."""
        print(message, details)  # noqa T201

    def warning(self, message: str, details: dict[str, Any] | None = None):
        """Log a warning."""
        _print_warning(message)

    def log(self, message: str, details: dict[str, Any] | None = None):
        """Log a log."""
        print(message, details)  # noqa T201


def _print_warning(skk):
    print(f"\033[93m {skk}\033[00m")  # noqa T201
