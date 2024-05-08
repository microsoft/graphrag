# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import Field

import graphrag.config.defaults as defs
from graphrag.config.enums import TextEmbeddingTarget

from .llm_config import LLMConfig


class TextEmbeddingConfig(LLMConfig):
    """Configuration section for text embeddings."""

    batch_size: int = Field(
        description="The batch size to use.", default=defs.EMBEDDING_BATCH_SIZE
    )
    batch_max_tokens: int = Field(
        description="The batch max tokens to use.",
        default=defs.EMBEDDING_BATCH_MAX_TOKENS,
    )
    target: TextEmbeddingTarget = Field(
        description="The target to use. 'all' or 'required'.",
        default=defs.EMBEDDING_TARGET,
    )
    skip: list[str] = Field(description="The specific embeddings to skip.", default=[])
    vector_store: dict | None = Field(
        description="The vector storage configuration", default=None
    )
    strategy: dict | None = Field(
        description="The override strategy to use.", default=None
    )

    def resolved_strategy(self) -> dict:
        """Get the resolved text embedding strategy."""
        from graphrag.index.verbs.text.embed import TextEmbedStrategyType

        return self.strategy or {
            "type": TextEmbedStrategyType.openai,
            "llm": self.llm.model_dump(),
            **self.parallelization.model_dump(),
            "batch_size": self.batch_size,
            "batch_max_tokens": self.batch_max_tokens,
        }
