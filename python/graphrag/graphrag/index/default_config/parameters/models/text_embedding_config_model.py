#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""Parameterization settings for the default configuration."""
from enum import Enum

from pydantic import Field

from .llm_config_model import LLMConfigModel


class TextEmbeddingTarget(str, Enum):
    """The target to use for text embeddings."""

    all = "all"
    required = "required"


class TextEmbeddingConfigModel(LLMConfigModel):
    """Configuration section for text embeddings."""

    batch_size: int | None = Field(description="The batch size to use.", default=16)
    batch_max_tokens: int | None = Field(
        description="The batch max tokens to use.", default=8191
    )
    target: TextEmbeddingTarget | None = Field(
        description="The target to use. 'all' or 'required'.",
        default=None,
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
