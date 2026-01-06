# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing input file type enum."""

from enum import StrEnum


class InputFileType(StrEnum):
    """The input file type for the pipeline."""

    Csv = "csv"
    """The CSV input type."""
    Text = "text"
    """The text input type."""
    Json = "json"
    """The JSON input type."""

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'
