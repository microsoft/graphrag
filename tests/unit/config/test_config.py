# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from pathlib import Path

import pytest
from pydantic import ValidationError

import graphrag.config.defaults as defs
from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.config.enums import AzureAuthType, LLMType
from graphrag.config.load_config import load_config
from tests.unit.config.utils import (
    DEFAULT_CHAT_MODEL_CONFIG,
    DEFAULT_EMBEDDING_MODEL_CONFIG,
    DEFAULT_MODEL_CONFIG,
    assert_graphrag_configs,
    get_default_graphrag_config,
)


def test_missing_default_chat_model_config() -> None:
    with pytest.raises(ValidationError):
        create_graphrag_config()


def test_missing_default_embedding_model_config() -> None:
    models_config = {
        defs.DEFAULT_CHAT_MODEL_ID: DEFAULT_CHAT_MODEL_CONFIG,
    }

    with pytest.raises(ValidationError):
        create_graphrag_config({"models": models_config})


def test_missing_openai_required_api_key() -> None:
    model_config_missing_api_key = {
        defs.DEFAULT_CHAT_MODEL_ID: {
            "type": LLMType.OpenAIChat,
            "model": defs.LLM_MODEL,
        },
        defs.DEFAULT_EMBEDDING_MODEL_ID: DEFAULT_EMBEDDING_MODEL_CONFIG,
    }

    # API Key required for OpenAIChat
    with pytest.raises(ValidationError):
        create_graphrag_config({"models": model_config_missing_api_key})

    # API Key required for OpenAIEmbedding
    model_config_missing_api_key[defs.DEFAULT_CHAT_MODEL_ID]["type"] = (
        LLMType.OpenAIEmbedding
    )
    with pytest.raises(ValidationError):
        create_graphrag_config({"models": model_config_missing_api_key})


def test_missing_azure_api_key() -> None:
    model_config_missing_api_key = {
        defs.DEFAULT_CHAT_MODEL_ID: {
            "type": LLMType.AzureOpenAIChat,
            "azure_auth_type": AzureAuthType.APIKey,
            "model": defs.LLM_MODEL,
            "api_base": "some_api_base",
            "api_version": "some_api_version",
            "deployment_name": "some_deployment_name",
        },
        defs.DEFAULT_EMBEDDING_MODEL_ID: DEFAULT_EMBEDDING_MODEL_CONFIG,
    }

    with pytest.raises(ValidationError):
        create_graphrag_config({"models": model_config_missing_api_key})

    # API Key not required for managed identity
    model_config_missing_api_key[defs.DEFAULT_CHAT_MODEL_ID]["azure_auth_type"] = (
        AzureAuthType.ManagedIdentity
    )
    create_graphrag_config({"models": model_config_missing_api_key})


base_azure_model_config = {
    "type": LLMType.AzureOpenAIChat,
    "azure_auth_type": AzureAuthType.ManagedIdentity,
    "model": defs.LLM_MODEL,
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


def test_load_minimal_config() -> None:
    cwd = Path(__file__).parent
    root_dir = (cwd / "fixtures" / "minimal_config").resolve()
    expected = get_default_graphrag_config()
    expected.root_dir = str(root_dir)
    actual = load_config(root_dir=root_dir)
    assert_graphrag_configs(actual, expected)


def test_load_config_missing_env_vars() -> None:
    cwd = Path(__file__).parent
    root_dir = (cwd / "fixtures" / "minimal_config_missing_env_var").resolve()
    with pytest.raises(KeyError):
        load_config(root_dir=root_dir)
