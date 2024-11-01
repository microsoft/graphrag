# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'PipelineCacheConfig', 'PipelineFileCacheConfig' and 'PipelineMemoryCacheConfig' models."""

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

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'


class InputFileType(str, Enum):
    """The input file type for the pipeline."""

    csv = "csv"
    """The CSV input type."""
    text = "text"
    """The text input type."""

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


class StorageType(str, Enum):
    """The storage type for the pipeline."""

    file = "file"
    """The file storage type."""
    memory = "memory"
    """The memory storage type."""
    blob = "blob"
    """The blob storage type."""

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


class TextEmbeddingTarget(str, Enum):
    """The target to use for text embeddings."""

    all = "all"
    required = "required"
    none = "none"

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'


class LLMType(str, Enum):
    """LLMType enum class definition."""

    # Embeddings
    OpenAIEmbedding = "openai_embedding"
    AzureOpenAIEmbedding = "azure_openai_embedding"

    # Raw Completion
    OpenAI = "openai"
    AzureOpenAI = "azure_openai"

    # Chat Completion
    OpenAIChat = "openai_chat"
    AzureOpenAIChat = "azure_openai_chat"

    # Debug
    StaticResponse = "static_response"

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'
