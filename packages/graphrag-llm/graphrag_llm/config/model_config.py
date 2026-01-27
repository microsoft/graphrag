# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Language model configuration."""

import logging
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from graphrag_llm.config.metrics_config import MetricsConfig
from graphrag_llm.config.rate_limit_config import RateLimitConfig
from graphrag_llm.config.retry_config import RetryConfig
from graphrag_llm.config.types import AuthMethod, LLMProviderType

logger = logging.getLogger(__name__)


class ModelConfig(BaseModel):
    """Configuration for a language model."""

    model_config = ConfigDict(extra="allow")
    """Allow extra fields to support custom LLM provider implementations."""

    type: str = Field(
        default=LLMProviderType.LiteLLM,
        description="The type of LLM provider to use. (default: litellm)",
    )

    model_provider: str = Field(
        description="The provider of the model, e.g., 'openai', 'azure', etc.",
    )

    model: str = Field(
        description="The specific model to use, e.g., 'gpt-4o', 'gpt-3.5-turbo', etc.",
    )

    call_args: dict[str, Any] = Field(
        default_factory=dict,
        description="Base keyword arguments to pass to the model provider's API.",
    )

    api_base: str | None = Field(
        default=None,
        description="The base URL for the API, required for some providers like Azure.",
    )

    api_version: str | None = Field(
        default=None,
        description="The version of the API to use.",
    )

    api_key: str | None = Field(
        default=None,
        description="API key for authentication with the model provider.",
    )

    auth_method: AuthMethod = Field(
        default=AuthMethod.ApiKey,
        description="The authentication method to use. (default: api_key)",
    )

    azure_deployment_name: str | None = Field(
        default=None,
        description="The deployment name for Azure models.",
    )

    retry: RetryConfig | None = Field(
        default=None,
        description="Configuration for the retry strategy.",
    )

    rate_limit: RateLimitConfig | None = Field(
        default=None,
        description="Configuration for the rate limit behavior.",
    )

    metrics: MetricsConfig | None = Field(
        default_factory=MetricsConfig,
        description="Specify and configure the metric services.",
    )

    mock_responses: list[str] | list[float] = Field(
        default_factory=list,
        description="List of mock responses for testing.",
    )

    def _validate_lite_llm_config(self) -> None:
        """Validate LiteLLM specific configuration."""
        if self.model_provider == "azure" and not self.api_base:
            msg = "api_base must be specified with the 'azure' model provider."
            raise ValueError(msg)

        if self.model_provider != "azure" and self.azure_deployment_name is not None:
            msg = "azure_deployment_name should not be specified for non-Azure model providers."
            raise ValueError(msg)

        if self.auth_method == AuthMethod.AzureManagedIdentity:
            if self.api_key is not None:
                msg = "api_key should not be set when using Azure Managed Identity."
                raise ValueError(msg)
        elif not self.api_key:
            msg = "api_key must be set when auth_method=api_key."
            raise ValueError(msg)

    @model_validator(mode="after")
    def _validate_model(self):
        """Validate model configuration after initialization."""
        if self.type == LLMProviderType.LiteLLM:
            self._validate_lite_llm_config()
        return self
