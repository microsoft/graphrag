# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'prepend_metadata' function."""


def add_metadata(
    text: str,
    metadata: dict,
    delimiter: str = ": ",
    line_delimiter: str = "\n",
    append: bool = False,
) -> str:
    """Add metadata to the given text, prepending by default. This utility writes the dict as rows of key/value pairs."""
    metadata_str = (
        line_delimiter.join(f"{k}{delimiter}{v}" for k, v in metadata.items())
        + line_delimiter
    )
    return text + metadata_str if append else metadata_str + text
