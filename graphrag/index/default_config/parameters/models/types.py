# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Types for models."""

from enum import Enum


class TextEmbeddingTarget(str, Enum):
    """The target to use for text embeddings."""

    all = "all"
    required = "required"
