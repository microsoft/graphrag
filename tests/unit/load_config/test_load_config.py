# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Unit tests for graphrag-config.load_config."""

import os
from pathlib import Path

import pytest
from graphrag_common.config import ConfigParsingError, load_config
from pydantic import ValidationError

from .config import TestConfigModel


def test_load_config_validation():
    """Test loading config validation."""

    with pytest.raises(
        FileNotFoundError,
    ):
        _ = load_config(TestConfigModel, "non_existent_config.yaml")

    config_directory = Path(__file__).parent / "fixtures"
    invalid_config_formatting_path = config_directory / "invalid_config_format.yaml"

    with pytest.raises(
        FileNotFoundError,
    ):
        _ = load_config(
            config_initializer=TestConfigModel,
            config_path=invalid_config_formatting_path,
            dot_env_path="non_existent.env",
        )

    # Using yaml to parse invalid json formatting
    with pytest.raises(
        ConfigParsingError,
    ):
        _ = load_config(TestConfigModel, invalid_config_formatting_path)

    invalid_config_path = config_directory / "invalid_config.yaml"

    # Test validation error from config model
    with pytest.raises(
        ValidationError,
    ):
        _ = load_config(
            config_initializer=TestConfigModel,
            config_path=invalid_config_path,
            set_cwd=False,
        )


def test_load_config():
    """Test loading configuration."""

    config_directory = Path(__file__).parent / "fixtures"
    config_path = config_directory / "settings.yaml"

    # Load from dir
    config = load_config(
        config_initializer=TestConfigModel, config_path=config_directory, set_cwd=False
    )

    assert config.name == "test_name"
    assert config.value == 100
    assert config.nested.nested_str == "nested_value"
    assert config.nested.nested_int == 42
    assert len(config.nested_list) == 2
    assert config.nested_list[0].nested_str == "list_value_1"
    assert config.nested_list[0].nested_int == 7
    assert config.nested_list[1].nested_str == "list_value_2"
    assert config.nested_list[1].nested_int == 8

    # Should not have changed directories
    root_repo_dir = Path(__file__).parent.parent.parent.parent.resolve()
    assert Path.cwd().resolve() == root_repo_dir

    config = load_config(
        config_initializer=TestConfigModel,
        config_path=config_path,
        set_cwd=False,
    )

    assert config.name == "test_name"
    assert config.value == 100
    assert config.nested.nested_str == "nested_value"
    assert config.nested.nested_int == 42
    assert len(config.nested_list) == 2
    assert config.nested_list[0].nested_str == "list_value_1"
    assert config.nested_list[0].nested_int == 7
    assert config.nested_list[1].nested_str == "list_value_2"
    assert config.nested_list[1].nested_int == 8

    overrides = {
        "value": 65537,
        "nested": {"nested_int": 84},
        "nested_list": [
            {"nested_str": "overridden_list_value_1", "nested_int": 23},
        ],
    }

    cwd = Path.cwd()
    config_with_overrides = load_config(
        config_initializer=TestConfigModel,
        config_path=config_path,
        overrides=overrides,
    )

    # Should have changed directories to the config file location
    assert Path.cwd() == config_directory
    assert (
        Path("some/new/path").resolve()
        == (config_directory / "some/new/path").resolve()
    )
    # Reset cwd
    os.chdir(cwd)

    assert config_with_overrides.name == "test_name"
    assert config_with_overrides.value == 65537
    assert config_with_overrides.nested.nested_str == "nested_value"
    assert config_with_overrides.nested.nested_int == 84
    assert len(config_with_overrides.nested_list) == 1
    assert config_with_overrides.nested_list[0].nested_str == "overridden_list_value_1"
    assert config_with_overrides.nested_list[0].nested_int == 23

    config_with_env_vars_path = config_directory / "config_with_env.yaml"

    # Config contains env vars that do not exist
    # and no .env file is provided
    with pytest.raises(
        ConfigParsingError,
    ):
        _ = load_config(
            config_initializer=TestConfigModel,
            config_path=config_with_env_vars_path,
            load_dot_env_file=False,
            set_cwd=False,
        )

    env_path = config_directory / "test.env"
    config_with_env_vars = load_config(
        config_initializer=TestConfigModel,
        config_path=config_with_env_vars_path,
        dot_env_path=env_path,
    )

    assert config_with_env_vars.name == "env_name"
    assert config_with_env_vars.value == 100
    assert config_with_env_vars.nested.nested_str == "nested_value"
    assert config_with_env_vars.nested.nested_int == 42
    assert len(config_with_env_vars.nested_list) == 2
    assert config_with_env_vars.nested_list[0].nested_str == "list_value_1"
    assert config_with_env_vars.nested_list[0].nested_int == 7
    assert config_with_env_vars.nested_list[1].nested_str == "list_value_2"
    assert config_with_env_vars.nested_list[1].nested_int == 8
