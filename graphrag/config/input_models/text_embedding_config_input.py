# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from typing_extensions import NotRequired

from graphrag.config.enums import (
    TextEmbeddingTarget,
)
from graphrag.config.input_models.llm_config_input import LLMConfigInput


class TextEmbeddingConfigInput(LLMConfigInput):
    """Configuration section for text embeddings."""

    batch_size: NotRequired[int | str | None]
    batch_max_tokens: NotRequired[int | str | None]
    target: NotRequired[TextEmbeddingTarget | str | None]
    skip: NotRequired[list[str] | str | None]
    vector_store: NotRequired[dict | None]
    strategy: NotRequired[dict | None]
