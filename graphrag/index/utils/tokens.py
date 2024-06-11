# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Utilities for working with tokens."""

import tiktoken

DEFAULT_ENCODING_NAME = "cl100k_base"


def num_tokens_from_string(
    string: str, model: str | None = None, encoding_name: str | None = None
) -> int:
    """Return the number of tokens in a text string."""
    if model is not None:
        encoding = tiktoken.encoding_for_model(model)
    else:
        encoding = tiktoken.get_encoding(encoding_name or DEFAULT_ENCODING_NAME)
    return len(encoding.encode(string))


def string_from_tokens(
    tokens: list[int], model: str | None = None, encoding_name: str | None = None
) -> str:
    """Return a text string from a list of tokens."""
    if model is not None:
        encoding = tiktoken.encoding_for_model(model)
    elif encoding_name is not None:
        encoding = tiktoken.get_encoding(encoding_name)
    else:
        msg = "Either model or encoding_name must be specified."
        raise ValueError(msg)
    return encoding.decode(tokens)
