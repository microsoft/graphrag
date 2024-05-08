# Copyright (c) 2024 Microsoft Corporation.

"""A base class for OpenAI-based LLMs."""

from openai import (
    AsyncAzureOpenAI,
    AsyncOpenAI,
)

OpenAIClientTypes = AsyncOpenAI | AsyncAzureOpenAI
