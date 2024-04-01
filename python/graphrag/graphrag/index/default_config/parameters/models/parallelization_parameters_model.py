#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

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
