# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import os
from pathlib import Path
from unittest import mock

import pytest
from pydantic import ValidationError

import graphrag.config.defaults as defs
from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.config.enums import AuthType, ModelType
from graphrag.config.load_config import load_config
from tests.unit.config.utils import (
    DEFAULT_EMBEDDING_MODEL_CONFIG,
    DEFAULT_MODEL_CONFIG,
    FAKE_API_KEY,
    assert_graphrag_configs,
    get_default_graphrag_config,
)


def test_missing_openai_required_api_key() -> None:
    model_config_missing_api_key = {
        defs.DEFAULT_CHAT_MODEL_ID: {
            "type": ModelType.OpenAIChat,
            "model": defs.DEFAULT_CHAT_MODEL,
        },
        defs.DEFAULT_EMBEDDING_MODEL_ID: DEFAULT_EMBEDDING_MODEL_CONFIG,
    }

    # API Key required for OpenAIChat
    with pytest.raises(ValidationError):
        create_graphrag_config({"models": model_config_missing_api_key})

    # API Key required for OpenAIEmbedding
    model_config_missing_api_key[defs.DEFAULT_CHAT_MODEL_ID]["type"] = (
        ModelType.OpenAIEmbedding
    )
    with pytest.raises(ValidationError):
        create_graphrag_config({"models": model_config_missing_api_key})


def test_missing_azure_api_key() -> None:
    model_config_missing_api_key = {
        defs.DEFAULT_CHAT_MODEL_ID: {
            "type": ModelType.AzureOpenAIChat,
            "auth_type": AuthType.APIKey,
            "model": defs.DEFAULT_CHAT_MODEL,
            "api_base": "some_api_base",
            "api_version": "some_api_version",
            "deployment_name": "some_deployment_name",
        },
        defs.DEFAULT_EMBEDDING_MODEL_ID: DEFAULT_EMBEDDING_MODEL_CONFIG,
    }

    with pytest.raises(ValidationError):
        create_graphrag_config({"models": model_config_missing_api_key})

    # API Key not required for managed identity
    model_config_missing_api_key[defs.DEFAULT_CHAT_MODEL_ID]["auth_type"] = (
        AuthType.AzureManagedIdentity
    )
    create_graphrag_config({"models": model_config_missing_api_key})


def test_conflicting_auth_type() -> None:
    model_config_invalid_auth_type = {
        defs.DEFAULT_CHAT_MODEL_ID: {
            "auth_type": AuthType.AzureManagedIdentity,
            "type": ModelType.OpenAIChat,
            "model": defs.DEFAULT_CHAT_MODEL,
        },
        defs.DEFAULT_EMBEDDING_MODEL_ID: DEFAULT_EMBEDDING_MODEL_CONFIG,
    }

    with pytest.raises(ValidationError):
        create_graphrag_config({"models": model_config_invalid_auth_type})


def test_conflicting_azure_api_key() -> None:
    model_config_conflicting_api_key = {
        defs.DEFAULT_CHAT_MODEL_ID: {
            "type": ModelType.AzureOpenAIChat,
            "auth_type": AuthType.AzureManagedIdentity,
            "model": defs.DEFAULT_CHAT_MODEL,
            "api_base": "some_api_base",
            "api_version": "some_api_version",
            "deployment_name": "some_deployment_name",
            "api_key": "THIS_SHOULD_NOT_BE_SET_WHEN_USING_MANAGED_IDENTITY",
        },
        defs.DEFAULT_EMBEDDING_MODEL_ID: DEFAULT_EMBEDDING_MODEL_CONFIG,
    }

    with pytest.raises(ValidationError):
        create_graphrag_config({"models": model_config_conflicting_api_key})


base_azure_model_config = {
    "type": ModelType.AzureOpenAIChat,
    "auth_type": AuthType.AzureManagedIdentity,
    "model": defs.DEFAULT_CHAT_MODEL,
    "api_base": "some_api_base",
    "api_version": "some_api_version",
    "deployment_name": "some_deployment_name",
}


def test_missing_azure_api_base() -> None:
    missing_api_base_config = base_azure_model_config.copy()
    del missing_api_base_config["api_base"]

    with pytest.raises(ValidationError):
        create_graphrag_config({
            "models": {
                defs.DEFAULT_CHAT_MODEL_ID: missing_api_base_config,
                defs.DEFAULT_EMBEDDING_MODEL_ID: DEFAULT_EMBEDDING_MODEL_CONFIG,
            }
        })


def test_missing_azure_api_version() -> None:
    missing_api_version_config = base_azure_model_config.copy()
    del missing_api_version_config["api_version"]

    with pytest.raises(ValidationError):
        create_graphrag_config({
            "models": {
                defs.DEFAULT_CHAT_MODEL_ID: missing_api_version_config,
                defs.DEFAULT_EMBEDDING_MODEL_ID: DEFAULT_EMBEDDING_MODEL_CONFIG,
            }
        })


def test_missing_azure_deployment_name() -> None:
    missing_deployment_name_config = base_azure_model_config.copy()
    del missing_deployment_name_config["deployment_name"]

    with pytest.raises(ValidationError):
        create_graphrag_config({
            "models": {
                defs.DEFAULT_CHAT_MODEL_ID: missing_deployment_name_config,
                defs.DEFAULT_EMBEDDING_MODEL_ID: DEFAULT_EMBEDDING_MODEL_CONFIG,
            }
        })


def test_default_config() -> None:
    expected = get_default_graphrag_config()
    actual = create_graphrag_config({"models": DEFAULT_MODEL_CONFIG})
    assert_graphrag_configs(actual, expected)


@mock.patch.dict(os.environ, {"CUSTOM_API_KEY": FAKE_API_KEY}, clear=True)
def test_load_minimal_config() -> None:
    cwd = Path(__file__).parent
    root_dir = (cwd / "fixtures" / "minimal_config").resolve()
    expected = get_default_graphrag_config(str(root_dir))
    actual = load_config(root_dir=root_dir)
    assert_graphrag_configs(actual, expected)


@mock.patch.dict(os.environ, {"CUSTOM_API_KEY": FAKE_API_KEY}, clear=True)
def test_load_config_with_cli_overrides() -> None:
    cwd = Path(__file__).parent
    root_dir = (cwd / "fixtures" / "minimal_config").resolve()
    output_dir = "some_output_dir"
    expected_output_base_dir = root_dir / output_dir
    expected = get_default_graphrag_config(str(root_dir))
    expected.output.base_dir = str(expected_output_base_dir)
    actual = load_config(
        root_dir=root_dir,
        cli_overrides={"output.base_dir": output_dir},
    )
    assert_graphrag_configs(actual, expected)


def test_load_config_missing_env_vars() -> None:
    cwd = Path(__file__).parent
    root_dir = (cwd / "fixtures" / "minimal_config_missing_env_var").resolve()
    with pytest.raises(KeyError):
        load_config(root_dir=root_dir)
