# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from datashaper import AsyncType
from pydantic import BaseModel, Field

from graphrag.index.default_config.parameters.defaults import DEFAULT_ASYNC_MODE

from .llm_parameters_model import LLMParametersModel
from .parallelization_parameters_model import ParallelizationParametersModel


class LLMConfigModel(BaseModel):
    """Base class for LLM-configured steps."""

    llm: LLMParametersModel = Field(
        description="The LLM configuration to use.", default=LLMParametersModel()
    )
    parallelization: ParallelizationParametersModel = Field(
        description="The parallelization configuration to use.",
        default=ParallelizationParametersModel(),
    )
    async_mode: AsyncType | None = Field(
        description="The async mode to use.", default=DEFAULT_ASYNC_MODE
    )
