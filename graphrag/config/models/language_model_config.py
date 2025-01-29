# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Language model configuration."""

import tiktoken
from pydantic import BaseModel, Field, model_validator

import graphrag.config.defaults as defs
from graphrag.config.enums import AsyncType, AuthType, LLMType
from graphrag.config.errors import (
    ApiKeyMissingError,
    AzureApiBaseMissingError,
    AzureApiVersionMissingError,
    AzureDeploymentNameMissingError,
    ConflictingSettingsError,
)


class LanguageModelConfig(BaseModel):
    """Language model configuration."""

    api_key: str | None = Field(
        description="The API key to use for the LLM service.",
        default=None,
    )

    def _validate_api_key(self) -> None:
        """Validate the API key.

        API Key is required when using OpenAI API
        or when using Azure API with API Key authentication.
        For the time being, this check is extra verbose for clarity.
        It will also through an exception if an API Key is provided
        when one is not expected such as the case of using Azure
        Managed Identity.

        Raises
        ------
        ApiKeyMissingError
            If the API key is missing and is required.
        """
        if self.auth_type == AuthType.APIKey and (
            self.api_key is None or self.api_key.strip() == ""
        ):
            raise ApiKeyMissingError(
                self.type.value,
                self.auth_type.value,
            )

        if (self.auth_type == AuthType.AzureManagedIdentity) and (
            self.api_key is not None and self.api_key.strip() != ""
        ):
            msg = "API Key should not be provided when using Azure Managed Identity. Please rerun `graphrag init` and remove the api_key when using Azure Managed Identity."
            raise ConflictingSettingsError(msg)

    auth_type: AuthType = Field(
        description="The authentication type.",
        default=defs.AUTH_TYPE,
    )

    def _validate_auth_type(self) -> None:
        """Validate the authentication type.

        auth_type must be api_key when using OpenAI and
        can be either api_key or azure_managed_identity when using AOI.

        Raises
        ------
        ConflictingSettingsError
            If the Azure authentication type conflicts with the model being used.
        """
        if self.auth_type == AuthType.AzureManagedIdentity and (
            self.type == LLMType.OpenAIChat or self.type == LLMType.OpenAIEmbedding
        ):
            msg = f"auth_type of azure_managed_identity is not supported for model type {self.type.value}. Please rerun `graphrag init` and set the auth_type to api_key."
            raise ConflictingSettingsError(msg)

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

    max_tokens: int = Field(
        description="The maximum number of tokens to generate.",
        default=defs.LLM_MAX_TOKENS,
    )
    temperature: float = Field(
        description="The temperature to use for token generation.",
        default=defs.LLM_TEMPERATURE,
    )
    top_p: float = Field(
        description="The top-p value to use for token generation.",
        default=defs.LLM_TOP_P,
    )
    n: int = Field(
        description="The number of completions to generate.",
        default=defs.LLM_N,
    )
    frequency_penalty: float = Field(
        description="The frequency penalty to use for token generation.",
        default=defs.LLM_FREQUENCY_PENALTY,
    )
    presence_penalty: float = Field(
        description="The presence penalty to use for token generation.",
        default=defs.LLM_PRESENCE_PENALTY,
    )
    request_timeout: float = Field(
        description="The request timeout to use.", default=defs.LLM_REQUEST_TIMEOUT
    )
    api_base: str | None = Field(
        description="The base URL for the LLM API.", default=None
    )

    def _validate_api_base(self) -> None:
        """Validate the API base.

        Required when using AOI.

        Raises
        ------
        AzureApiBaseMissingError
            If the API base is missing and is required.
        """
        if (
            self.type == LLMType.AzureOpenAIChat
            or self.type == LLMType.AzureOpenAIEmbedding
        ) and (self.api_base is None or self.api_base.strip() == ""):
            raise AzureApiBaseMissingError(self.type.value)

    api_version: str | None = Field(
        description="The version of the LLM API to use.", default=None
    )

    def _validate_api_version(self) -> None:
        """Validate the API version.

        Required when using AOI.

        Raises
        ------
        AzureApiBaseMissingError
            If the API base is missing and is required.
        """
        if (
            self.type == LLMType.AzureOpenAIChat
            or self.type == LLMType.AzureOpenAIEmbedding
        ) and (self.api_version is None or self.api_version.strip() == ""):
            raise AzureApiVersionMissingError(self.type.value)

    deployment_name: str | None = Field(
        description="The deployment name to use for the LLM service.", default=None
    )

    def _validate_deployment_name(self) -> None:
        """Validate the deployment name.

        Required when using AOI.

        Raises
        ------
        AzureDeploymentNameMissingError
            If the deployment name is missing and is required.
        """
        if (
            self.type == LLMType.AzureOpenAIChat
            or self.type == LLMType.AzureOpenAIEmbedding
        ) and (self.deployment_name is None or self.deployment_name.strip() == ""):
            raise AzureDeploymentNameMissingError(self.type.value)

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

    def _validate_azure_settings(self) -> None:
        """Validate the Azure settings.

        Raises
        ------
        AzureApiBaseMissingError
            If the API base is missing and is required.
        AzureApiVersionMissingError
            If the API version is missing and is required.
        AzureDeploymentNameMissingError
            If the deployment name is missing and is required.
        """
        self._validate_api_base()
        self._validate_api_version()
        self._validate_deployment_name()

    @model_validator(mode="after")
    def _validate_model(self):
        self._validate_auth_type()
        self._validate_api_key()
        self._validate_azure_settings()
        self._validate_encoding_model()
        return self
