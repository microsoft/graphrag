# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from datashaper import AsyncType
from typing_extensions import NotRequired, TypedDict

from .llm_parameters_input import LLMParametersInput
from .parallelization_parameters_input import ParallelizationParametersInput


class LLMConfigInput(TypedDict):
    """Base class for LLM-configured steps."""

    llm: NotRequired[LLMParametersInput | None]
    parallelization: NotRequired[ParallelizationParametersInput | None]
    async_mode: NotRequired[AsyncType | str | None]
