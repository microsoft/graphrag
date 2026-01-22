# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License


"""GraphRAG LLM configuration types."""

from enum import StrEnum


class LLMProviderType(StrEnum):
    """Enum for LLM provider types."""

    LiteLLM = "litellm"
    MockLLM = "mock"


class AuthMethod(StrEnum):
    """Enum for authentication methods."""

    ApiKey = "api_key"
    AzureManagedIdentity = "azure_managed_identity"


class MetricsProcessorType(StrEnum):
    """Enum for built-in MetricsProcessor types."""

    Default = "default"


class MetricsWriterType(StrEnum):
    """Enum for built-in MetricsWriter types."""

    Log = "log"
    File = "file"


class MetricsStoreType(StrEnum):
    """Enum for built-in MetricsStore types."""

    Memory = "memory"


class RateLimitType(StrEnum):
    """Enum for built-in RateLimit types."""

    SlidingWindow = "sliding_window"


class RetryType(StrEnum):
    """Enum for built-in Retry types."""

    ExponentialBackoff = "exponential_backoff"
    Immediate = "immediate"


class TemplateEngineType(StrEnum):
    """Enum for built-in TemplateEngine types."""

    Jinja = "jinja"


class TemplateManagerType(StrEnum):
    """Enum for built-in TemplateEngine types."""

    File = "file"


class TokenizerType(StrEnum):
    """Enum for tokenizer types."""

    LiteLLM = "litellm"
    Tiktoken = "tiktoken"
