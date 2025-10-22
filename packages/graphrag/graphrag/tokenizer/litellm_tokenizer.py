# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""LiteLLM Tokenizer."""

from litellm import decode, encode  # type: ignore

from graphrag.tokenizer.tokenizer import Tokenizer


class LitellmTokenizer(Tokenizer):
    """LiteLLM Tokenizer."""

    def __init__(self, model_name: str) -> None:
        """Initialize the LiteLLM Tokenizer.

        Args
        ----
            model_name (str): The name of the LiteLLM model to use for tokenization.
        """
        self.model_name = model_name

    def encode(self, text: str) -> list[int]:
        """Encode the given text into a list of tokens.

        Args
        ----
            text (str): The input text to encode.

        Returns
        -------
            list[int]: A list of tokens representing the encoded text.
        """
        return encode(model=self.model_name, text=text)

    def decode(self, tokens: list[int]) -> str:
        """Decode a list of tokens back into a string.

        Args
        ----
            tokens (list[int]): A list of tokens to decode.

        Returns
        -------
            str: The decoded string from the list of tokens.
        """
        return decode(model=self.model_name, tokens=tokens)
