# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.config.defaults import graphrag_config_defaults
from graphrag.config.models.language_model_config import LanguageModelConfig


class TextEmbeddingConfig(BaseModel):
    """Configuration section for text embeddings."""

    model_id: str = Field(
        description="The model ID to use for text embeddings.",
        default=graphrag_config_defaults.embed_text.model_id,
    )
    vector_store_id: str = Field(
        description="The vector store ID to use for text embeddings.",
        default=graphrag_config_defaults.embed_text.vector_store_id,
    )
    batch_size: int = Field(
        description="The batch size to use.",
        default=graphrag_config_defaults.embed_text.batch_size,
    )
    batch_max_tokens: int = Field(
        description="The batch max tokens to use.",
        default=graphrag_config_defaults.embed_text.batch_max_tokens,
    )
    names: list[str] = Field(
        description="The specific embeddings to perform.",
        default=graphrag_config_defaults.embed_text.names,
    )
    strategy: dict | None = Field(
        description="The override strategy to use.",
        default=graphrag_config_defaults.embed_text.strategy,
    )

    def resolved_strategy(self, model_config: LanguageModelConfig) -> dict:
        """Get the resolved text embedding strategy."""
        from graphrag.index.operations.embed_text import (
            TextEmbedStrategyType,
        )

        return self.strategy or {
            "type": TextEmbedStrategyType.openai,
            "llm": model_config.model_dump(),
            "num_threads": model_config.concurrent_requests,
            "batch_size": self.batch_size,
            "batch_max_tokens": self.batch_max_tokens,
        }
