# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from __future__ import annotations

import typing

import tiktoken


def num_tokens(text: str, token_encoder: typing.Optional[tiktoken.Encoding] = None) -> int:
    """Return the number of tokens in the given text."""
    token_encoder = token_encoder or tiktoken.get_encoding("cl100k_base")
    return token_encoder.encode(text).__len__()
