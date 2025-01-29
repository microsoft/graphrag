# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Base class for noun phrase extractors."""

from abc import ABCMeta, abstractmethod


class BaseNounPhraseExtractor(metaclass=ABCMeta):
    """Abstract base class for noun phrase extractors."""

    def __init__(
        self,
        model_name: str | None,
        exclude_nouns: list[str] | None = None,
        max_word_length: int = 15,
        word_delimiter: str = " ",
    ) -> None:
        self.model_name = model_name
        self.max_word_length = max_word_length
        if exclude_nouns is None:
            exclude_nouns = []
        self.exclude_nouns = [noun.upper() for noun in exclude_nouns]
        self.word_delimiter = word_delimiter

    @abstractmethod
    def extract(self, text: str) -> list[str]:
        """
        Extract noun phrases from text.

        Args:
            text: Text.

        Returns: List of noun phrases.
        """
