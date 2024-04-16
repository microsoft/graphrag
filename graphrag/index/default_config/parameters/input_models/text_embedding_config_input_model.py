# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from typing_extensions import NotRequired

from graphrag.index.default_config.parameters.models.text_embedding_config_model import (
    TextEmbeddingTarget,
)

from .llm_config_input_model import LLMConfigInputModel


class TextEmbeddingConfigInputModel(LLMConfigInputModel):
    """Configuration section for text embeddings."""

    batch_size: NotRequired[int | str | None]
    batch_max_tokens: NotRequired[int | str | None]
    target: NotRequired[TextEmbeddingTarget | str | None]
    skip: NotRequired[list[str] | str | None]
    vector_store: NotRequired[dict | None]
    strategy: NotRequired[dict | None]
