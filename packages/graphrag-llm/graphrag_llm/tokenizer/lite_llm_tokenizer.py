# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""LiteLLM Tokenizer."""

from typing import Any

from litellm import decode, encode  # type: ignore

from graphrag_llm.tokenizer.tokenizer import Tokenizer


class LiteLLMTokenizer(Tokenizer):
    """LiteLLM Tokenizer."""

    _model_id: str

    def __init__(self, *, model_id: str, **kwargs: Any) -> None:
        """Initialize the LiteLLM Tokenizer.

        Args
        ----
            model_id: str
                The LiteLLM model ID, e.g., "openai/gpt-4o".
        """
        self._model_id = model_id

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
        return encode(model=self._model_id, text=text)

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
        return decode(model=self._model_id, tokens=tokens)
