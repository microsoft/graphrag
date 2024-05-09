# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Status Reporter for orchestration."""

from abc import ABCMeta, abstractmethod
from typing import Any


class StatusReporter(metaclass=ABCMeta):
    """Provides a way to report status updates from the pipeline."""

    @abstractmethod
    def error(self, message: str, details: dict[str, Any] | None = None):
        """Report an error."""

    @abstractmethod
    def warning(self, message: str, details: dict[str, Any] | None = None):
        """Report a warning."""

    @abstractmethod
    def log(self, message: str, details: dict[str, Any] | None = None):
        """Report a log."""


class ConsoleStatusReporter(StatusReporter):
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
