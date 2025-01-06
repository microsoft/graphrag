# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Language model configuration."""

import tiktoken
from pydantic import BaseModel, Field, model_validator

import graphrag.config.defaults as defs
from graphrag.config.enums import AsyncType, LLMType


class ModelConfig(BaseModel):
    """Language model configuration."""

    id: str = Field(
        description="A user friendly ID of the model used elsewhere in GraphRAGConfig for selecting models."
    )
    api_key: str | None = Field(
        description="The API key to use for the LLM service.",
        default=None,
    )
    type: LLMType = Field(description="The type of LLM model to use.")
    model: str = Field(description="The LLM model to use.")
    encoding_model: str = Field(description="The encoding model to use", default="")

    def _validate_encoding_model(self) -> None:
        """Validate the encoding model.

        Raises
        ------
        KeyError
            If the model name is not recognized.
        """
        if self.encoding_model.strip() == "":
            self.encoding_model = tiktoken.encoding_name_for_model(self.model)

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
    n: int | None = Field(
        description="The number of completions to generate.",
        default=defs.LLM_N,
    )
    frequency_penalty: float | None = Field(
        description="The frequency penalty to use for token generation.",
        default=defs.LLM_FREQUENCY_PENALTY,
    )
    presence_penalty: float | None = Field(
        description="The presence penalty to use for token generation.",
        default=defs.LLM_PRESENCE_PENALTY,
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
    deployment_name: str | None = Field(
        description="The deployment name to use for the LLM service.", default=None
    )
    organization: str | None = Field(
        description="The organization to use for the LLM service.", default=None
    )
    proxy: str | None = Field(
        description="The proxy to use for the LLM service.", default=None
    )
    audience: str | None = Field(
        description="Azure resource URI to use with managed identity for the llm connection.",
        default=None,
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
    responses: list[str | BaseModel] | None = Field(
        default=None, description="Static responses to use in mock mode."
    )
    parallelization_stagger: float = Field(
        description="The stagger to use for the LLM service.",
        default=defs.PARALLELIZATION_STAGGER,
    )
    parallelization_num_threads: int = Field(
        description="The number of threads to use for the LLM service.",
        default=defs.PARALLELIZATION_NUM_THREADS,
    )
    async_mode: AsyncType = Field(
        description="The async mode to use.", default=defs.ASYNC_MODE
    )

    @model_validator(mode="after")
    def _validate_model(self):
        self._validate_encoding_model()
        return self
