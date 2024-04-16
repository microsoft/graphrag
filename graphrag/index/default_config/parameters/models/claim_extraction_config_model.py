# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from pydantic import Field

from graphrag.index.default_config.parameters.defaults import (
    DEFAULT_CLAIM_DESCRIPTION,
    DEFAULT_CLAIM_MAX_GLEANINGS,
)

from .llm_config_model import LLMConfigModel


class ClaimExtractionConfigModel(LLMConfigModel):
    """Configuration section for claim extraction."""

    prompt: str | None = Field(
        description="The claim extraction prompt to use.", default=None
    )
    description: str | None = Field(
        description="The claim description to use.",
        default=DEFAULT_CLAIM_DESCRIPTION,
    )
    max_gleanings: int | None = Field(
        description="The maximum number of entity gleanings to use.",
        default=DEFAULT_CLAIM_MAX_GLEANINGS,
    )
    strategy: dict | None = Field(
        description="The override strategy to use.", default=None
    )
