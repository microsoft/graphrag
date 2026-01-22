# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Tokenizer Abstract Base Class."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from graphrag_llm.types import LLMCompletionMessagesParam


class Tokenizer(ABC):
    """Tokenizer Abstract Base Class."""

    @abstractmethod
    def __init__(self, **kwargs: Any) -> None:
        """Initialize the LiteLLM Tokenizer."""

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    def num_prompt_tokens(
        self,
        messages: "LLMCompletionMessagesParam",
    ) -> int:
        """Count the number of tokens in a prompt for a given model.

        Counts the number of tokens used for roles, names, and content in the messages.

        modeled after: https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb

        Args
        ----
            messages: LLMCompletionMessagesParam
                The messages comprising the prompt. Can either be a string or a list of message dicts.

        Returns
        -------
            int: The number of tokens in the prompt.
        """
        total_tokens = 3  # overhead for reply
        tokens_per_message = 3  # fixed overhead per message
        tokens_per_name = 1  # fixed overhead per name field

        if isinstance(messages, str):
            return (
                self.num_tokens(messages)
                + total_tokens
                + tokens_per_message
                + tokens_per_name
            )

        for message in messages:
            total_tokens += tokens_per_message
            if not isinstance(message, dict):
                message = message.model_dump()
            for key, value in message.items():
                if key == "content":
                    if isinstance(value, str):
                        total_tokens += self.num_tokens(value)
                    elif isinstance(value, list):
                        for part in value:
                            if isinstance(part, dict) and "text" in part:
                                total_tokens += self.num_tokens(part["text"])
                elif key == "role":
                    total_tokens += self.num_tokens(str(value))
                elif key == "name":
                    total_tokens += self.num_tokens(str(value)) + tokens_per_name
        return total_tokens

    def num_tokens(self, text: str) -> int:
        """Return the number of tokens in the given text.

        Args
        ----
            text: str
                The input text to analyze.

        Returns
        -------
            int: The number of tokens in the input text.
        """
        return len(self.encode(text))
