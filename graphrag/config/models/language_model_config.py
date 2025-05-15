# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Language model configuration."""

from typing import Literal

import tiktoken
from pydantic import BaseModel, Field, model_validator

from graphrag.config.defaults import language_model_defaults
from graphrag.config.enums import AsyncType, AuthType, ModelType
from graphrag.config.errors import (
    ApiKeyMissingError,
    AzureApiBaseMissingError,
    AzureApiVersionMissingError,
    AzureDeploymentNameMissingError,
    ConflictingSettingsError,
)
from graphrag.language_model.factory import ModelFactory


class LanguageModelConfig(BaseModel):
    """Language model configuration."""

    api_key: str | None = Field(
        description="The API key to use for the LLM service.",
        default=language_model_defaults.api_key,
    )

    def _validate_api_key(self) -> None:
        """Validate the API key.

        API Key is required when using OpenAI API
        or when using Azure API with API Key authentication.
        For the time being, this check is extra verbose for clarity.
        It will also raise an exception if an API Key is provided
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
                self.type,
                self.auth_type.value,
            )

        if (self.auth_type == AuthType.AzureManagedIdentity) and (
            self.api_key is not None and self.api_key.strip() != ""
        ):
            msg = "API Key should not be provided when using Azure Managed Identity. Please rerun `graphrag init` and remove the api_key when using Azure Managed Identity."
            raise ConflictingSettingsError(msg)

    auth_type: AuthType = Field(
        description="The authentication type.",
        default=language_model_defaults.auth_type,
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
            self.type == ModelType.OpenAIChat or self.type == ModelType.OpenAIEmbedding
        ):
            msg = f"auth_type of azure_managed_identity is not supported for model type {self.type}. Please rerun `graphrag init` and set the auth_type to api_key."
            raise ConflictingSettingsError(msg)

    type: ModelType | str = Field(description="The type of LLM model to use.")

    def _validate_type(self) -> None:
        """Validate the model type.

        Raises
        ------
        KeyError
            If the model name is not recognized.
        """
        # Type should be contained by the registered models
        if not ModelFactory.is_supported_model(self.type):
            msg = f"Model type {self.type} is not recognized, must be one of {ModelFactory.get_chat_models() + ModelFactory.get_embedding_models()}."
            raise KeyError(msg)

    model: str = Field(description="The LLM model to use.")
    encoding_model: str = Field(
        description="The encoding model to use",
        default=language_model_defaults.encoding_model,
    )

    def _validate_encoding_model(self) -> None:
        """Validate the encoding model.

        Raises
        ------
        KeyError
            If the model name is not recognized.
        """
        if self.encoding_model.strip() == "":
            self.encoding_model = tiktoken.encoding_name_for_model(self.model)

    api_base: str | None = Field(
        description="The base URL for the LLM API.",
        default=language_model_defaults.api_base,
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
            self.type == ModelType.AzureOpenAIChat
            or self.type == ModelType.AzureOpenAIEmbedding
        ) and (self.api_base is None or self.api_base.strip() == ""):
            raise AzureApiBaseMissingError(self.type)

    api_version: str | None = Field(
        description="The version of the LLM API to use.",
        default=language_model_defaults.api_version,
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
            self.type == ModelType.AzureOpenAIChat
            or self.type == ModelType.AzureOpenAIEmbedding
        ) and (self.api_version is None or self.api_version.strip() == ""):
            raise AzureApiVersionMissingError(self.type)

    deployment_name: str | None = Field(
        description="The deployment name to use for the LLM service.",
        default=language_model_defaults.deployment_name,
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
            self.type == ModelType.AzureOpenAIChat
            or self.type == ModelType.AzureOpenAIEmbedding
        ) and (self.deployment_name is None or self.deployment_name.strip() == ""):
            raise AzureDeploymentNameMissingError(self.type)

    organization: str | None = Field(
        description="The organization to use for the LLM service.",
        default=language_model_defaults.organization,
    )
    proxy: str | None = Field(
        description="The proxy to use for the LLM service.",
        default=language_model_defaults.proxy,
    )
    audience: str | None = Field(
        description="Azure resource URI to use with managed identity for the llm connection.",
        default=language_model_defaults.audience,
    )
    model_supports_json: bool | None = Field(
        description="Whether the model supports JSON output mode.",
        default=language_model_defaults.model_supports_json,
    )
    request_timeout: float = Field(
        description="The request timeout to use.",
        default=language_model_defaults.request_timeout,
    )
    tokens_per_minute: int | Literal["auto"] | None = Field(
        description="The number of tokens per minute to use for the LLM service.",
        default=language_model_defaults.tokens_per_minute,
    )
    requests_per_minute: int | Literal["auto"] | None = Field(
        description="The number of requests per minute to use for the LLM service.",
        default=language_model_defaults.requests_per_minute,
    )
    retry_strategy: str = Field(
        description="The retry strategy to use for the LLM service.",
        default=language_model_defaults.retry_strategy,
    )
    max_retries: int = Field(
        description="The maximum number of retries to use for the LLM service.",
        default=language_model_defaults.max_retries,
    )
    max_retry_wait: float = Field(
        description="The maximum retry wait to use for the LLM service.",
        default=language_model_defaults.max_retry_wait,
    )
    concurrent_requests: int = Field(
        description="Whether to use concurrent requests for the LLM service.",
        default=language_model_defaults.concurrent_requests,
    )
    async_mode: AsyncType = Field(
        description="The async mode to use.", default=language_model_defaults.async_mode
    )
    responses: list[str | BaseModel] | None = Field(
        default=language_model_defaults.responses,
        description="Static responses to use in mock mode.",
    )
    max_tokens: int | None = Field(
        description="The maximum number of tokens to generate.",
        default=language_model_defaults.max_tokens,
    )
    temperature: float = Field(
        description="The temperature to use for token generation.",
        default=language_model_defaults.temperature,
    )
    max_completion_tokens: int | None = Field(
        description="The maximum number of tokens to consume. This includes reasoning tokens for the o* reasoning models.",
        default=language_model_defaults.max_completion_tokens,
    )
    reasoning_effort: str | None = Field(
        description="Level of effort OpenAI reasoning models should expend. Supported options are 'low', 'medium', 'high'; and OAI defaults to 'medium'.",
        default=language_model_defaults.reasoning_effort,
    )
    top_p: float = Field(
        description="The top-p value to use for token generation.",
        default=language_model_defaults.top_p,
    )
    n: int = Field(
        description="The number of completions to generate.",
        default=language_model_defaults.n,
    )
    frequency_penalty: float = Field(
        description="The frequency penalty to use for token generation.",
        default=language_model_defaults.frequency_penalty,
    )
    presence_penalty: float = Field(
        description="The presence penalty to use for token generation.",
        default=language_model_defaults.presence_penalty,
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
        self._validate_type()
        self._validate_auth_type()
        self._validate_api_key()
        self._validate_azure_settings()
        self._validate_encoding_model()
        return self
