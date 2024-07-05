# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""LLM Parameters model."""

from pydantic import BaseModel, ConfigDict, Field

import graphrag.config.defaults as defs
from graphrag.config.enums import LLMType


class LLMParameters(BaseModel):
    """LLM Parameters model."""

    model_config = ConfigDict(protected_namespaces=(), extra="allow")
    api_key: str | None = Field(
        description="The API key to use for the LLM service.",
        default=None,
    )
    type: LLMType = Field(
        description="The type of LLM model to use.", default=defs.LLM_TYPE
    )
    model: str = Field(description="The LLM model to use.", default=defs.LLM_MODEL)
    max_tokens: int | None = Field(
        description="The maximum number of tokens to generate.",
        default=defs.LLM_MAX_TOKENS,
    )
    temperature: float | None = Field(
        description="The temperature to use for token generation.",
        default=defs.LLM_TEMPERATURE,
    )
    top_p: float | None = Field(
        description="The top-p value to use for token generation.",
        default=defs.LLM_TOP_P,
    )
    request_timeout: float = Field(
        description="The request timeout to use.", default=defs.LLM_REQUEST_TIMEOUT
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
    cognitive_services_endpoint: str | None = Field(
        description="The endpoint to reach cognitives services.", default=None
    )
    deployment_name: str | None = Field(
        description="The deployment name to use for the LLM service.", default=None
    )
    model_supports_json: bool | None = Field(
        description="Whether the model supports JSON output mode.", default=None
    )
    tokens_per_minute: int = Field(
        description="The number of tokens per minute to use for the LLM service.",
        default=defs.LLM_TOKENS_PER_MINUTE,
    )
    requests_per_minute: int = Field(
        description="The number of requests per minute to use for the LLM service.",
        default=defs.LLM_REQUESTS_PER_MINUTE,
    )
    max_retries: int = Field(
        description="The maximum number of retries to use for the LLM service.",
        default=defs.LLM_MAX_RETRIES,
    )
    max_retry_wait: float = Field(
        description="The maximum retry wait to use for the LLM service.",
        default=defs.LLM_MAX_RETRY_WAIT,
    )
    sleep_on_rate_limit_recommendation: bool = Field(
        description="Whether to sleep on rate limit recommendations.",
        default=defs.LLM_SLEEP_ON_RATE_LIMIT_RECOMMENDATION,
    )
    concurrent_requests: int = Field(
        description="Whether to use concurrent requests for the LLM service.",
        default=defs.LLM_CONCURRENT_REQUESTS,
    )
