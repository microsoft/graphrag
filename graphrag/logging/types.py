# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Types for status reporting."""

from enum import Enum


class ReporterType(str, Enum):
    """The type of reporter to use."""

    RICH = "rich"
    PRINT = "print"
    NONE = "none"

    def __str__(self):
        """Return the string representation of the enum value."""
        return self.value
