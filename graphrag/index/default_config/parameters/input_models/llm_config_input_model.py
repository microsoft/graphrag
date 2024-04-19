# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from datashaper import AsyncType
from typing_extensions import NotRequired, TypedDict

from .llm_parameters_input_model import LLMParametersInputModel
from .parallelization_parameters_input_model import ParallelizationParametersInputModel


class LLMConfigInputModel(TypedDict):
    """Base class for LLM-configured steps."""

    llm: NotRequired[LLMParametersInputModel | None]
    parallelization: NotRequired[ParallelizationParametersInputModel | None]
    async_mode: NotRequired[AsyncType | str | None]
