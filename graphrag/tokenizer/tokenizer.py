# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Tokenizer Abstract Base Class."""

from abc import ABC, abstractmethod


class Tokenizer(ABC):
    """Tokenizer Abstract Base Class."""

    @abstractmethod
    def encode(self, text: str) -> list[int]:
        """Encode the given text into a list of tokens.

        Args
        ----
            text (str): The input text to encode.

        Returns
        -------
            list[int]: A list of tokens representing the encoded text.
        """
        msg = "The encode method must be implemented by subclasses."
        raise NotImplementedError(msg)

    @abstractmethod
    def decode(self, tokens: list[int]) -> str:
        """Decode a list of tokens back into a string.

        Args
        ----
            tokens (list[int]): A list of tokens to decode.

        Returns
        -------
            str: The decoded string from the list of tokens.
        """
        msg = "The decode method must be implemented by subclasses."
        raise NotImplementedError(msg)
