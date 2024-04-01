#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""A base class for OpenAI-based LLMs."""
from openai import (
    AsyncAzureOpenAI,
    AsyncOpenAI,
)

OpenAIClientTypes = AsyncOpenAI | AsyncAzureOpenAI
