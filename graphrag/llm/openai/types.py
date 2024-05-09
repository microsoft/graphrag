# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A base class for OpenAI-based LLMs."""

from openai import (
    AsyncAzureOpenAI,
    AsyncOpenAI,
)

OpenAIClientTypes = AsyncOpenAI | AsyncAzureOpenAI
