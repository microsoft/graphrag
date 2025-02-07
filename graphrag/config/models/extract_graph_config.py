# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pathlib import Path

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs
from graphrag.config.models.language_model_config import LanguageModelConfig


class ExtractGraphConfig(BaseModel):
    """Configuration section for entity extraction."""

    prompt: str | None = Field(
        description="The entity extraction prompt to use.", default=None
    )
    entity_types: list[str] = Field(
        description="The entity extraction entity types to use.",
        default=defs.EXTRACT_GRAPH_ENTITY_TYPES,
    )
    max_gleanings: int = Field(
        description="The maximum number of entity gleanings to use.",
        default=defs.EXTRACT_GRAPH_MAX_GLEANINGS,
    )
    strategy: dict | None = Field(
        description="Override the default entity extraction strategy", default=None
    )
    encoding_model: str | None = Field(
        default=None, description="The encoding model to use."
    )
    model_id: str = Field(
        description="The model ID to use for text embeddings.",
        default=defs.EXTRACT_GRAPH_MODEL_ID,
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
            "stagger": model_config.parallelization_stagger,
            "num_threads": model_config.parallelization_num_threads,
            "extraction_prompt": (Path(root_dir) / self.prompt).read_text(
                encoding="utf-8"
            )
            if self.prompt
            else None,
            "max_gleanings": self.max_gleanings,
            "encoding_name": model_config.encoding_model,
        }
