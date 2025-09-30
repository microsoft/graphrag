# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Tiktoken Tokenizer."""

import tiktoken

from graphrag.tokenizer.tokenizer import Tokenizer


class TiktokenTokenizer(Tokenizer):
    """Tiktoken Tokenizer."""

    def __init__(self, encoding_name: str) -> None:
        """Initialize the Tiktoken Tokenizer.

        Args
        ----
            encoding_name (str): The name of the Tiktoken encoding to use for tokenization.
        """
        self.encoding = tiktoken.get_encoding(encoding_name)

    def encode(self, text: str) -> list[int]:
        """Encode the given text into a list of tokens.

        Args
        ----
            text (str): The input text to encode.

        Returns
        -------
            list[int]: A list of tokens representing the encoded text.
        """
        return self.encoding.encode(text)

    def decode(self, tokens: list[int]) -> str:
        """Decode a list of tokens back into a string.

        Args
        ----
            tokens (list[int]): A list of tokens to decode.

        Returns
        -------
            str: The decoded string from the list of tokens.
        """
        return self.encoding.decode(tokens)
