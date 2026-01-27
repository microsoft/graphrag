# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A collection of useful built-in transformers you can use for chunking."""

from collections.abc import Callable
from typing import Any


def add_metadata(
    metadata: dict[str, Any],
    delimiter: str = ": ",
    line_delimiter: str = "\n",
    append: bool = False,
) -> Callable[[str], str]:
    """Add metadata to the given text, prepending by default. This utility writes the dict as rows of key/value pairs."""

    def transformer(text: str) -> str:
        metadata_str = (
            line_delimiter.join(f"{k}{delimiter}{v}" for k, v in metadata.items())
            + line_delimiter
        )
        return text + metadata_str if append else metadata_str + text

    return transformer
