# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Types for prompt tuning."""

from enum import Enum


class DocSelectionType(str, Enum):
    """The type of document selection to use."""

    ALL = "all"
    RANDOM = "random"
    TOP = "top"
    AUTO = "auto"

    def __str__(self):
        """Return the string representation of the enum value."""
        return self.value
