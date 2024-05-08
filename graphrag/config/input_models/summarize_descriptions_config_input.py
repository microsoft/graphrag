# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from typing_extensions import NotRequired

from .llm_config_input import LLMConfigInput


class SummarizeDescriptionsConfigInput(LLMConfigInput):
    """Configuration section for description summarization."""

    prompt: NotRequired[str | None]
    max_length: NotRequired[int | str | None]
    strategy: NotRequired[dict | None]
