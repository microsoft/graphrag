# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pathlib import Path

from pydantic import BaseModel, Field

from graphrag.config.defaults import graphrag_config_defaults
from graphrag.config.models.language_model_config import LanguageModelConfig


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
    strategy: dict | None = Field(
        description="Override the default entity extraction strategy",
        default=graphrag_config_defaults.extract_graph.strategy,
    )

    def resolved_strategy(
        self, root_dir: str, model_config: LanguageModelConfig
    ) -> dict:
        """Get the resolved entity extraction strategy."""
        from graphrag.index.operations.extract_graph.typing import (
            ExtractEntityStrategyType,
        )

        return self.strategy or {
            "type": ExtractEntityStrategyType.graph_intelligence,
            "llm": model_config.model_dump(),
            "extraction_prompt": (Path(root_dir) / self.prompt).read_text(
                encoding="utf-8"
            )
            if self.prompt
            else None,
            "max_gleanings": self.max_gleanings,
        }
