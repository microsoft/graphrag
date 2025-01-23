# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs


class ExtractGraphNLPConfig(BaseModel):
    """Configuration section for graph extraction via NLP."""

    max_word_length: int = Field(
        description="The max word length for NLP parsing.",
        default=defs.EXTRACT_GRAPH_NLP_MAX_WORD_LENGTH,
    )

    normalize_edge_weights: bool = Field(
        description="Whether to normalize edge weights.",
        default=defs.EXTRACT_GRAPH_NLP_NORMALIZE_EDGE_WEIGHTS,
    )
