# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs
from graphrag.config.enums import TextEmbeddingTarget
from graphrag.config.models.language_model_config import LanguageModelConfig


class TextEmbeddingConfig(BaseModel):
    """Configuration section for text embeddings."""

    batch_size: int = Field(
        description="The batch size to use.", default=defs.EMBEDDING_BATCH_SIZE
    )
    batch_max_tokens: int = Field(
        description="The batch max tokens to use.",
        default=defs.EMBEDDING_BATCH_MAX_TOKENS,
    )
    target: TextEmbeddingTarget = Field(
        description="The target to use. 'all', 'required', 'selected', or 'none'.",
        default=defs.EMBEDDING_TARGET,
    )
    names: list[str] = Field(
        description="The specific embeddings to perform.", default=[]
    )
    strategy: dict | None = Field(
        description="The override strategy to use.", default=None
    )
    model_id: str = Field(
        description="The model ID to use for text embeddings.",
        default=defs.EMBEDDING_MODEL_ID,
    )

    def resolved_strategy(self, model_config: LanguageModelConfig) -> dict:
        """Get the resolved text embedding strategy."""
        from graphrag.index.operations.embed_text import (
            TextEmbedStrategyType,
        )

        return self.strategy or {
            "type": TextEmbedStrategyType.openai,
            "llm": model_config.model_dump(),
            "stagger": model_config.parallelization_stagger,
            "num_threads": model_config.parallelization_num_threads,
            "batch_size": self.batch_size,
            "batch_max_tokens": self.batch_max_tokens,
        }
