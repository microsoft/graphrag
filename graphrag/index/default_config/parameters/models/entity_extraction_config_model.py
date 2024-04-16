# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from pydantic import Field

from graphrag.index.default_config.parameters.defaults import (
    DEFAULT_ENTITY_EXTRACTION_ENTITY_TYPES,
    DEFAULT_ENTITY_EXTRACTION_MAX_GLEANINGS,
)
from graphrag.index.verbs.entities.extraction import ExtractEntityStrategyType

from .llm_config_model import LLMConfigModel


class EntityExtractionConfigModel(LLMConfigModel):
    """Configuration section for entity extraction."""

    prompt: str | None = Field(
        description="The entity extraction prompt to use.", default=None
    )
    entity_types: list[str] = Field(
        description="The entity extraction entity types to use.",
        default=DEFAULT_ENTITY_EXTRACTION_ENTITY_TYPES,
    )
    max_gleanings: int = Field(
        description="The maximum number of entity gleanings to use.",
        default=DEFAULT_ENTITY_EXTRACTION_MAX_GLEANINGS,
    )
    strategy: dict | None = Field(
        description="Override the default entity extraction strategy", default=None
    )

    def resolved_strategy(self, encoding_model: str) -> dict:
        """Get the resolved entity extraction strategy."""
        return self.strategy or {
            "type": ExtractEntityStrategyType.graph_intelligence,
            "llm": self.llm.model_dump(),
            **self.parallelization.model_dump(),
            "extraction_prompt": self.prompt,
            "max_gleanings": self.max_gleanings,
            # It's prechunked in create_base_text_units
            "encoding_name": encoding_model,
            "prechunked": True,
        }
