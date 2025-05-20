# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing config enums."""

from __future__ import annotations

from enum import Enum


class CacheType(str, Enum):
    """The cache configuration type for the pipeline."""

    file = "file"
    """The file cache configuration type."""
    memory = "memory"
    """The memory cache configuration type."""
    none = "none"
    """The none cache configuration type."""
    blob = "blob"
    """The blob cache configuration type."""
    cosmosdb = "cosmosdb"
    """The cosmosdb cache configuration type"""

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'


class InputFileType(str, Enum):
    """The input file type for the pipeline."""

    csv = "csv"
    """The CSV input type."""
    text = "text"
    """The text input type."""
    json = "json"
    """The JSON input type."""

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'


class InputType(str, Enum):
    """The input type for the pipeline."""

    file = "file"
    """The file storage type."""
    blob = "blob"
    """The blob storage type."""

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'


class OutputType(str, Enum):
    """The output type for the pipeline."""

    file = "file"
    """The file output type."""
    memory = "memory"
    """The memory output type."""
    blob = "blob"
    """The blob output type."""
    cosmosdb = "cosmosdb"
    """The cosmosdb output type"""

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'


class ReportingType(str, Enum):
    """The reporting configuration type for the pipeline."""

    file = "file"
    """The file reporting configuration type."""
    console = "console"
    """The console reporting configuration type."""
    blob = "blob"
    """The blob reporting configuration type."""

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'


class ModelType(str, Enum):
    """LLMType enum class definition."""

    # Embeddings
    OpenAIEmbedding = "openai_embedding"
    AzureOpenAIEmbedding = "azure_openai_embedding"

    # Chat Completion
    OpenAIChat = "openai_chat"
    AzureOpenAIChat = "azure_openai_chat"

    # Debug
    MockChat = "mock_chat"
    MockEmbedding = "mock_embedding"

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'


class AuthType(str, Enum):
    """AuthType enum class definition."""

    APIKey = "api_key"
    AzureManagedIdentity = "azure_managed_identity"


class AsyncType(str, Enum):
    """Enum for the type of async to use."""

    AsyncIO = "asyncio"
    Threaded = "threaded"


class ChunkStrategyType(str, Enum):
    """ChunkStrategy class definition."""

    tokens = "tokens"
    sentence = "sentence"

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'


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
