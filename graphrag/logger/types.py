# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Logging types."""

from enum import Enum


class LoggerType(str, Enum):
    """The type of logger to use."""

    RICH = "rich"
    PRINT = "print"
    NONE = "none"

    def __str__(self):
        """Return a string representation of the enum value."""
        return self.value
