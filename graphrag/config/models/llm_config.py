# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from datashaper import AsyncType
from pydantic import BaseModel, Field

from graphrag.config.defaults import DEFAULT_ASYNC_MODE

from .llm_parameters import LLMParameters
from .parallelization_parameters import ParallelizationParameters


class LLMConfig(BaseModel):
    """Base class for LLM-configured steps."""

    llm: LLMParameters = Field(
        description="The LLM configuration to use.", default=LLMParameters()
    )
    parallelization: ParallelizationParameters = Field(
        description="The parallelization configuration to use.",
        default=ParallelizationParameters(),
    )
    async_mode: AsyncType = Field(
        description="The async mode to use.", default=DEFAULT_ASYNC_MODE
    )
