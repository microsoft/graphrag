# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field

from graphrag.config.defaults import graphrag_config_defaults
from graphrag.prompts.index.extract_graph import GRAPH_EXTRACTION_PROMPT


@dataclass
class ExtractGraphPrompts:
    """Graph extraction prompt templates."""

    extraction_prompt: str


class ExtractGraphConfig(BaseModel):
    """Configuration section for entity extraction."""

    model_id: str = Field(
        description="The model ID to use for text embeddings.",
        default=graphrag_config_defaults.extract_graph.model_id,
    )
    prompt: str | None = Field(
        description="The entity extraction prompt to use.",
        default=graphrag_config_defaults.extract_graph.prompt,
    )
    entity_types: list[str] = Field(
        description="The entity extraction entity types to use.",
        default=graphrag_config_defaults.extract_graph.entity_types,
    )
    max_gleanings: int = Field(
        description="The maximum number of entity gleanings to use.",
        default=graphrag_config_defaults.extract_graph.max_gleanings,
    )

    def resolved_prompts(self, root_dir: str) -> ExtractGraphPrompts:
        """Get the resolved graph extraction prompts."""
        return ExtractGraphPrompts(
            extraction_prompt=(Path(root_dir) / self.prompt).read_text(encoding="utf-8")
            if self.prompt
            else GRAPH_EXTRACTION_PROMPT,
        )
