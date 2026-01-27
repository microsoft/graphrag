# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.config.defaults import graphrag_config_defaults


class EmbedTextConfig(BaseModel):
    """Configuration section for text embeddings."""

    embedding_model_id: str = Field(
        description="The model ID to use for text embeddings.",
        default=graphrag_config_defaults.embed_text.embedding_model_id,
    )
    model_instance_name: str = Field(
        description="The model singleton instance name. This primarily affects the cache storage partitioning.",
        default=graphrag_config_defaults.embed_text.model_instance_name,
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
