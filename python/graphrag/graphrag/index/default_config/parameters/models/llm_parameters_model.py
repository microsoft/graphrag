#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""LLM Parameters model."""

from pydantic import BaseModel, ConfigDict, Field


class LLMParametersModel(BaseModel):
    """LLM Parameters model."""

    model_config = ConfigDict(protected_namespaces=(), extra="allow")
    api_key: str | None = Field(
        description="The API key to use for the LLM service.", default=None
    )
    type: str | None = Field(description="The type of LLM model to use.", default=None)
    model: str | None = Field(description="The LLM model to use.", default=None)
    max_tokens: int | None = Field(
        description="The maximum number of tokens to generate.", default=None
    )
    request_timeout: float | None = Field(
        description="The request timeout to use.", default=None
    )
    api_base: str | None = Field(
        description="The base URL for the LLM API.", default=None
    )
    api_version: str | None = Field(
        description="The version of the LLM API to use.", default=None
    )
    organization: str | None = Field(
        description="The organization to use for the LLM service.", default=None
    )
    proxy: str | None = Field(
        description="The proxy to use for the LLM service.", default=None
    )
    deployment_name: str | None = Field(
        description="The deployment name to use for the LLM service.", default=None
    )
    model_supports_json: bool | None = Field(
        description="Whether the model supports JSON output mode.", default=None
    )
    tokens_per_minute: int | None = Field(
        description="The number of tokens per minute to use for the LLM service.",
        default=None,
    )
    requests_per_minute: int | None = Field(
        description="The number of requests per minute to use for the LLM service.",
        default=None,
    )
    max_retries: int | None = Field(
        description="The maximum number of retries to use for the LLM service.",
        default=None,
    )
    max_retry_wait: float | None = Field(
        description="The maximum retry wait to use for the LLM service.", default=None
    )
    sleep_on_rate_limit_recommendation: bool | None = Field(
        description="Whether to sleep on rate limit recommendations.", default=None
    )
    concurrent_requests: int | None = Field(
        description="Whether to use concurrent requests for the LLM service.",
        default=None,
    )
