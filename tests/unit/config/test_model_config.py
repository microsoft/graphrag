# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Test model configuration loading."""

import pytest
from graphrag_llm.config import AuthMethod, LLMProviderType, ModelConfig
from pydantic import ValidationError


def test_litellm_provider_validation() -> None:
    """Test that missing required parameters raise validation errors."""

    with pytest.raises(ValidationError):
        _ = ModelConfig(
            type=LLMProviderType.LiteLLM,
            model_provider="openai",
            model="",
        )

    with pytest.raises(ValidationError):
        _ = ModelConfig(
            type=LLMProviderType.LiteLLM,
            model_provider="",
            model="gpt-4o",
        )

    with pytest.raises(
        ValueError,
        match="api_key must be set when auth_method=api_key\\.",
    ):
        _ = ModelConfig(
            type=LLMProviderType.LiteLLM,
            model_provider="openai",
            model="gpt-4o",
        )

    with pytest.raises(
        ValueError,
        match="azure_deployment_name should not be specified for non-Azure model providers\\.",
    ):
        _ = ModelConfig(
            type=LLMProviderType.LiteLLM,
            model_provider="openai",
            model="gpt-4o",
            azure_deployment_name="some-deployment",
        )

    with pytest.raises(
        ValueError,
        match="api_base must be specified with the 'azure' model provider\\.",
    ):
        _ = ModelConfig(
            type=LLMProviderType.LiteLLM,
            model_provider="azure",
            model="gpt-4o",
        )

    with pytest.raises(
        ValueError,
        match="api_key should not be set when using Azure Managed Identity\\.",
    ):
        _ = ModelConfig(
            type=LLMProviderType.LiteLLM,
            model_provider="azure",
            model="gpt-4o",
            azure_deployment_name="gpt-4o",
            api_base="https://my-azure-endpoint/",
            api_version="2024-06-01",
            auth_method=AuthMethod.AzureManagedIdentity,
            api_key="some-api-key",
        )

    with pytest.raises(
        ValueError,
        match="api_key must be set when auth_method=api_key\\.",
    ):
        _ = ModelConfig(
            type=LLMProviderType.LiteLLM,
            model_provider="azure",
            azure_deployment_name="gpt-4o",
            api_base="https://my-azure-endpoint/",
            api_version="2024-06-01",
            model="gpt-4o",
        )

    # pass validation
    _ = ModelConfig(
        type=LLMProviderType.LiteLLM,
        model_provider="openai",
        model="gpt-4o",
        api_key="NOT_A_REAL_API_KEY",
    )
    _ = ModelConfig(
        type=LLMProviderType.LiteLLM,
        model_provider="azure",
        model="gpt-4o",
        azure_deployment_name="gpt-4o",
        api_base="https://my-azure-endpoint/",
        api_key="NOT_A_REAL_API_KEY",
    )
    _ = ModelConfig(
        type=LLMProviderType.LiteLLM,
        model_provider="azure",
        model="gpt-4o",
        azure_deployment_name="gpt-4o",
        api_base="https://my-azure-endpoint/",
        api_version="2024-06-01",
        auth_method=AuthMethod.AzureManagedIdentity,
    )
