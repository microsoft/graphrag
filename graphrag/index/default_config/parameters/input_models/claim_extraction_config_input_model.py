# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from typing_extensions import NotRequired

from .llm_config_input_model import LLMConfigInputModel


class ClaimExtractionConfigInputModel(LLMConfigInputModel):
    """Configuration section for claim extraction."""

    prompt: NotRequired[str | None]
    description: NotRequired[str | None]
    max_gleanings: NotRequired[int | str | None]
    strategy: NotRequired[dict | None]
