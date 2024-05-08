# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from typing_extensions import NotRequired

from .llm_config_input import LLMConfigInput


class EntityExtractionConfigInput(LLMConfigInput):
    """Configuration section for entity extraction."""

    prompt: NotRequired[str | None]
    entity_types: NotRequired[list[str] | str | None]
    max_gleanings: NotRequired[int | str | None]
    strategy: NotRequired[dict | None]
