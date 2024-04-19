# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""LLM Parameters model."""

from pydantic import BaseModel, Field

from graphrag.index.default_config.parameters.defaults import (
    DEFAULT_PARALLELIZATION_NUM_THREADS,
    DEFAULT_PARALLELIZATION_STAGGER,
)


class ParallelizationParametersModel(BaseModel):
    """LLM Parameters model."""

    stagger: float = Field(
        description="The stagger to use for the LLM service.",
        default=DEFAULT_PARALLELIZATION_STAGGER,
    )
    num_threads: int = Field(
        description="The number of threads to use for the LLM service.",
        default=DEFAULT_PARALLELIZATION_NUM_THREADS,
    )
