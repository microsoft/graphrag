# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from pydantic import Field

from graphrag.index.default_config.parameters.defaults import (
    DEFAULT_ENTITY_EXTRACTION_ENTITY_TYPES,
    DEFAULT_ENTITY_EXTRACTION_MAX_GLEANINGS,
)

from .llm_config_model import LLMConfigModel


class EntityExtractionConfigModel(LLMConfigModel):
    """Configuration section for entity extraction."""

    prompt: str | None = Field(
        description="The entity extraction prompt to use.", default=None
    )
    entity_types: list[str] | None = Field(
        description="The entity extraction entity types to use.",
        default=DEFAULT_ENTITY_EXTRACTION_ENTITY_TYPES,
    )
    max_gleanings: int | None = Field(
        description="The maximum number of entity gleanings to use.",
        default=DEFAULT_ENTITY_EXTRACTION_MAX_GLEANINGS,
    )
    strategy: dict | None = Field(
        description="Override the default entity extraction strategy", default=None
    )
