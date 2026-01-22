# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing config enums."""

from __future__ import annotations

from enum import Enum


class ReportingType(str, Enum):
    """The reporting configuration type for the pipeline."""

    file = "file"
    """The file reporting configuration type."""
    blob = "blob"
    """The blob reporting configuration type."""

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'


class AsyncType(str, Enum):
    """Enum for the type of async to use."""

    AsyncIO = "asyncio"
    Threaded = "threaded"


class SearchMethod(Enum):
    """The type of search to run."""

    LOCAL = "local"
    GLOBAL = "global"
    DRIFT = "drift"
    BASIC = "basic"

    def __str__(self):
        """Return the string representation of the enum value."""
        return self.value


class IndexingMethod(str, Enum):
    """Enum for the type of indexing to perform."""

    Standard = "standard"
    """Traditional GraphRAG indexing, with all graph construction and summarization performed by a language model."""
    Fast = "fast"
    """Fast indexing, using NLP for graph construction and language model for summarization."""
    StandardUpdate = "standard-update"
    """Incremental update with standard indexing."""
    FastUpdate = "fast-update"
    """Incremental update with fast indexing."""


class NounPhraseExtractorType(str, Enum):
    """Enum for the noun phrase extractor options."""

    RegexEnglish = "regex_english"
    """Standard extractor using regex. Fastest, but limited to English."""
    Syntactic = "syntactic_parser"
    """Noun phrase extractor based on dependency parsing and NER using SpaCy."""
    CFG = "cfg"
    """Noun phrase extractor combining CFG-based noun-chunk extraction and NER."""


class ModularityMetric(str, Enum):
    """Enum for the modularity metric to use."""

    Graph = "graph"
    """Graph modularity metric."""

    LCC = "lcc"

    WeightedComponents = "weighted_components"
    """Weighted components modularity metric."""
