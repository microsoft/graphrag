# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from pydantic import Field

from graphrag.index.default_config.parameters.defaults import (
    DEFAULT_EMBEDDING_BATCH_MAX_TOKENS,
    DEFAULT_EMBEDDING_BATCH_SIZE,
    DEFAULT_EMBEDDING_TARGET,
)

from .llm_config_model import LLMConfigModel
from .types import TextEmbeddingTarget


class TextEmbeddingConfigModel(LLMConfigModel):
    """Configuration section for text embeddings."""

    batch_size: int | None = Field(
        description="The batch size to use.", default=DEFAULT_EMBEDDING_BATCH_SIZE
    )
    batch_max_tokens: int | None = Field(
        description="The batch max tokens to use.",
        default=DEFAULT_EMBEDDING_BATCH_MAX_TOKENS,
    )
    target: TextEmbeddingTarget | None = Field(
        description="The target to use. 'all' or 'required'.",
        default=DEFAULT_EMBEDDING_TARGET,
    )
    skip: list[str] | None = Field(
        description="The specific embeddings to skip.", default=[]
    )
    vector_store: dict | None = Field(
        description="The vector storage configuration", default=None
    )
    strategy: dict | None = Field(
        description="The override strategy to use.", default=None
    )
