# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration."""

from pydantic import Field

from .llm_config_model import LLMConfigModel


class CommunityReportsConfigModel(LLMConfigModel):
    """Configuration section for community reports."""

    prompt: str | None = Field(
        description="The community report extraction prompt to use.", default=None
    )
    max_length: int | None = Field(
        description="The community report maximum length in tokens.", default=None
    )
    max_input_length: int | None = Field(
        description="The maximum input length in tokens to use when generating reports.",
        default=None,
    )
    strategy: dict | None = Field(
        description="The override strategy to use.", default=None
    )
