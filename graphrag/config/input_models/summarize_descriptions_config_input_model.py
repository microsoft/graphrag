# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from typing_extensions import NotRequired

from .llm_config_input_model import LLMConfigInputModel


class SummarizeDescriptionsConfigInputModel(LLMConfigInputModel):
    """Configuration section for description summarization."""

    prompt: NotRequired[str | None]
    max_length: NotRequired[int | str | None]
    strategy: NotRequired[dict | None]
