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


@pytest.mark.parametrize("provider", ["github_copilot", "another_provider"])
def test_provider_managed_auth(provider: str) -> None:
    config = ModelConfig.model_validate({
        "model_provider": provider,
        "model": "model",
        "auth_method": "provider",
    })
    assert config.auth_method == AuthMethod.Provider
    assert config.api_key is None
    assert ModelConfig.model_validate(config.model_dump()) == config


@pytest.mark.parametrize("api_key", ["", "explicit-key"])
def test_provider_managed_auth_rejects_api_key(api_key: str) -> None:
    with pytest.raises(ValidationError, match="api_key should not be set"):
        ModelConfig(
            model_provider="github_copilot",
            model="gpt-4o",
            auth_method=AuthMethod.Provider,
            api_key=api_key,
        )


@pytest.mark.parametrize(
    "call_args",
    [
        {"api_key": None},
        {"api_key": "explicit-key"},
        {"api_token": "explicit-token"},
        {"azure_ad_token": "explicit-token"},
        {"azure_ad_token_provider": lambda: "explicit-token"},
        {"headers": {"Authorization": "Bearer explicit-token"}},
        {"extra_headers": {"API-Key": "explicit-key"}},
        {"extra_headers": {"x-api-key": "explicit-key"}},
    ],
)
def test_provider_managed_auth_rejects_credential_overrides(call_args) -> None:
    with pytest.raises(ValidationError, match="auth_method=provider"):
        ModelConfig(
            model_provider="github_copilot",
            model="gpt-4o",
            auth_method=AuthMethod.Provider,
            call_args=call_args,
        )


def test_provider_managed_auth_rejects_extra_credentials() -> None:
    with pytest.raises(ValidationError, match="azure_ad_token"):
        ModelConfig.model_validate({
            "model_provider": "github_copilot",
            "model": "gpt-4o",
            "auth_method": "provider",
            "azure_ad_token": "explicit-token",
        })


def test_provider_managed_auth_allows_normal_call_args() -> None:
    ModelConfig(
        model_provider="github_copilot",
        model="gpt-4o",
        auth_method=AuthMethod.Provider,
        call_args={"temperature": 0.1, "extra_headers": {"X-Initiator": "agent"}},
    )


@pytest.mark.parametrize("api_key", [None, ""])
def test_api_key_auth_still_requires_key(api_key: str | None) -> None:
    with pytest.raises(ValidationError, match="api_key must be set"):
        ModelConfig(model_provider="openai", model="gpt-4o", api_key=api_key)
