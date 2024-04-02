# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""LLM Parameters model."""

from pydantic import BaseModel, Field


class ParallelizationParametersModel(BaseModel):
    """LLM Parameters model."""

    stagger: float | None = Field(
        description="The stagger to use for the LLM service.", default=None
    )
    num_threads: int | None = Field(
        description="The number of threads to use for the LLM service.", default=None
    )
