# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Base class for noun phrase extractors."""

import logging
from abc import ABCMeta, abstractmethod

import spacy

log = logging.getLogger(__name__)


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

    @abstractmethod
    def __str__(self) -> str:
        """Return string representation of the extractor, used for cache key generation."""

    @staticmethod
    def load_spacy_model(
        model_name: str, exclude: list[str] | None = None
    ) -> spacy.language.Language:
        """Load a SpaCy model."""
        if exclude is None:
            exclude = []
        try:
            return spacy.load(model_name, exclude=exclude)
        except OSError:
            msg = f"Model `{model_name}` not found. Attempting to download..."
            log.info(msg)
            from spacy.cli.download import download

            download(model_name)
            return spacy.load(model_name, exclude=exclude)
