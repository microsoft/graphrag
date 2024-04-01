#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""The Datashaper OpenAI Utilities package."""
from .base import BaseLLM, CachingLLM, RateLimitingLLM
from .errors import RetriesExhaustedError
from .limiting import (
    CompositeLLMLimiter,
    LLMLimiter,
    NoopLLMLimiter,
    TpmRpmLLMLimiter,
    create_tpm_rpm_limiters,
)
from .mock import MockChatLLM, MockCompletionLLM
from .openai import (
    OpenAIChatLLM,
    OpenAIClientTypes,
    OpenAICompletionLLM,
    OpenAIConfiguration,
    OpenAIEmbeddingsLLM,
    create_openai_chat_llm,
    create_openai_client,
    create_openai_completion_llm,
    create_openai_embedding_llm,
)
from .types import (
    LLM,
    CompletionInput,
    CompletionLLM,
    CompletionOutput,
    EmbeddingInput,
    EmbeddingLLM,
    EmbeddingOutput,
    ErrorHandlerFn,
    IsResponseValidFn,
    LLMCache,
    LLMConfig,
    LLMInput,
    LLMInvocationFn,
    LLMInvocationResult,
    LLMOutput,
    OnCacheActionFn,
)

__all__ = [
    # Cache
    "LLMCache",
    # Callbacks
    "ErrorHandlerFn",
    "IsResponseValidFn",
    "LLMInvocationFn",
    "OnCacheActionFn",
    # Errors
    "RetriesExhaustedError",
    # LLM Types
    "LLM",
    "BaseLLM",
    "CachingLLM",
    "RateLimitingLLM",
    "LLMConfig",
    "CompletionLLM",
    "EmbeddingLLM",
    # LLM I/O Types
    "LLMInput",
    "LLMOutput",
    "LLMInvocationResult",
    "CompletionInput",
    "CompletionOutput",
    "EmbeddingInput",
    "EmbeddingOutput",
    # Limiters
    "create_tpm_rpm_limiters",
    "LLMLimiter",
    "NoopLLMLimiter",
    "TpmRpmLLMLimiter",
    "CompositeLLMLimiter",
    # OpenAI
    "OpenAIConfiguration",
    "OpenAIClientTypes",
    "create_openai_client",
    "OpenAIEmbeddingsLLM",
    "OpenAIChatLLM",
    "OpenAICompletionLLM",
    "create_openai_chat_llm",
    "create_openai_completion_llm",
    "create_openai_embedding_llm",
    # Mock
    "MockCompletionLLM",
    "MockChatLLM",
]
