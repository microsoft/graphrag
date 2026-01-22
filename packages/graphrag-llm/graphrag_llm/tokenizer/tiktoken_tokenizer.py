# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""LiteLLM Tokenizer."""

from typing import Any

import tiktoken

from graphrag_llm.tokenizer.tokenizer import Tokenizer


class TiktokenTokenizer(Tokenizer):
    """LiteLLM Tokenizer."""

    _encoding_name: str

    def __init__(self, *, encoding_name: str, **kwargs: Any) -> None:
        """Initialize the Tiktoken Tokenizer.

        Args
        ----
            encoding_name: str
                The encoding name, e.g., "gpt-4o".
        """
        self._encoding_name = encoding_name
        self._encoding = tiktoken.get_encoding(encoding_name)

    def encode(self, text: str) -> list[int]:
        """Encode the given text into a list of tokens.

        Args
        ----
            text: str
                The input text to encode.

        Returns
        -------
            list[int]: A list of tokens representing the encoded text.
        """
        return self._encoding.encode(text)

    def decode(self, tokens: list[int]) -> str:
        """Decode a list of tokens back into a string.

        Args
        ----
            tokens: list[int]
                A list of tokens to decode.

        Returns
        -------
            str: The decoded string from the list of tokens.
        """
        return self._encoding.decode(tokens)
