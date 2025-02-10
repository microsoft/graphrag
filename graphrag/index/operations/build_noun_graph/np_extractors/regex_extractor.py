# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Functions to analyze text data using SpaCy."""

import re
from typing import Any

import nltk
from textblob import TextBlob

from graphrag.index.operations.build_noun_graph.np_extractors.base import (
    BaseNounPhraseExtractor,
)
from graphrag.index.operations.build_noun_graph.np_extractors.resource_loader import (
    download_if_not_exists,
)


class RegexENNounPhraseExtractor(BaseNounPhraseExtractor):
    """Regular expression-based noun phrase extractor for English."""

    def __init__(
        self,
        exclude_nouns: list[str],
        max_word_length: int,
        word_delimiter: str,
    ):
        """
        Noun phrase extractor for English based on TextBlob's fast NP extractor, which uses a regex POS tagger and context-free grammars to detect noun phrases.

        NOTE: This is the extractor used in the first bencharmking of LazyGraphRAG but it only works for English.
        It is much faster but likely less accurate than the syntactic parser-based extractor.
        TODO: Reimplement this using SpaCy to remove TextBlob dependency.

        Args:
            max_word_length: Maximum length (in character) of each extracted word.
            word_delimiter: Delimiter for joining words.
        """
        super().__init__(
            model_name=None,
            max_word_length=max_word_length,
            exclude_nouns=exclude_nouns,
            word_delimiter=word_delimiter,
        )
        # download corpora
        download_if_not_exists("brown")
        download_if_not_exists("treebank")
        download_if_not_exists("averaged_perceptron_tagger_eng")

        # download tokenizers
        download_if_not_exists("punkt")
        download_if_not_exists("punkt_tab")

        # Preload the corpora to avoid lazy loading issues due to
        # race conditions when running multi-threaded jobs.
        nltk.corpus.brown.ensure_loaded()
        nltk.corpus.treebank.ensure_loaded()

    def extract(
        self,
        text: str,
    ) -> list[str]:
        """
        Extract noun phrases from text using regex patterns.

        Args:
            text: Text.

        Returns: List of noun phrases.
        """
        blob = TextBlob(text)
        proper_nouns = [token[0].upper() for token in blob.tags if token[1] == "NNP"]  # type: ignore
        tagged_noun_phrases = [
            self._tag_noun_phrases(chunk, proper_nouns)
            for chunk in blob.noun_phrases  # type: ignore
        ]

        filtered_noun_phrases = set()
        for tagged_np in tagged_noun_phrases:
            if (
                tagged_np["has_proper_nouns"]
                or len(tagged_np["cleaned_tokens"]) > 1
                or tagged_np["has_compound_words"]
            ) and tagged_np["has_valid_tokens"]:
                filtered_noun_phrases.add(tagged_np["cleaned_text"])
        return list(filtered_noun_phrases)

    def _tag_noun_phrases(
        self, noun_phrase: str, all_proper_nouns: list[str] | None = None
    ) -> dict[str, Any]:
        """Extract attributes of a noun chunk, to be used for filtering."""
        if all_proper_nouns is None:
            all_proper_nouns = []
        tokens = [token for token in re.split(r"[\s]+", noun_phrase) if len(token) > 0]
        cleaned_tokens = [
            token for token in tokens if token.upper() not in self.exclude_nouns
        ]
        has_proper_nouns = any(
            token.upper() in all_proper_nouns for token in cleaned_tokens
        )
        has_compound_words = any(
            "-" in token
            and len(token.strip()) > 1
            and len(token.strip().split("-")) > 1
            for token in cleaned_tokens
        )
        has_valid_tokens = all(
            re.match(r"^[a-zA-Z0-9\-]+\n?$", token) for token in cleaned_tokens
        ) and all(len(token) <= self.max_word_length for token in cleaned_tokens)
        return {
            "cleaned_tokens": cleaned_tokens,
            "cleaned_text": self.word_delimiter.join(token for token in cleaned_tokens)
            .replace("\n", "")
            .upper(),
            "has_proper_nouns": has_proper_nouns,
            "has_compound_words": has_compound_words,
            "has_valid_tokens": has_valid_tokens,
        }

    def __str__(self) -> str:
        """Return string representation of the extractor, used for cache key generation."""
        return f"regex_en_{self.exclude_nouns}_{self.max_word_length}_{self.word_delimiter}"
