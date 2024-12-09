# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Logging types.

This module defines the types of loggers that can be used.
"""

from enum import Enum


# Note: Code in this module was not included in the factory module because it negatively impacts the CLI experience.
class LoggerType(str, Enum):
    """The type of logger to use."""

    RICH = "rich"
    PRINT = "print"
    NONE = "none"

    def __str__(self):
        """Return a string representation of the enum value."""
        return self.value
