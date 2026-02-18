# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for entity resolution."""

from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field

from graphrag.config.defaults import graphrag_config_defaults
from graphrag.prompts.index.entity_resolution import ENTITY_RESOLUTION_PROMPT


@dataclass
class EntityResolutionPrompts:
    """Entity resolution prompt templates."""

    resolution_prompt: str


class EntityResolutionConfig(BaseModel):
    """Configuration section for entity resolution."""

    enabled: bool = Field(
        description="Whether to enable LLM-based entity resolution.",
        default=graphrag_config_defaults.entity_resolution.enabled,
    )
    completion_model_id: str = Field(
        description="The model ID to use for entity resolution.",
        default=graphrag_config_defaults.entity_resolution.completion_model_id,
    )
    model_instance_name: str = Field(
        description="The model singleton instance name. This primarily affects the cache storage partitioning.",
        default=graphrag_config_defaults.entity_resolution.model_instance_name,
    )
    prompt: str | None = Field(
        description="The entity resolution prompt to use.",
        default=graphrag_config_defaults.entity_resolution.prompt,
    )
    batch_size: int = Field(
        description="Maximum number of entity names to send to the LLM in each batch.",
        default=graphrag_config_defaults.entity_resolution.batch_size,
    )

    def resolved_prompts(self) -> EntityResolutionPrompts:
        """Get the resolved entity resolution prompts."""
        return EntityResolutionPrompts(
            resolution_prompt=Path(self.prompt).read_text(encoding="utf-8")
            if self.prompt
            else ENTITY_RESOLUTION_PROMPT,
        )
