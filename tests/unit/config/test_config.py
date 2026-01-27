# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import os
from pathlib import Path
from unittest import mock

from graphrag.config.load_config import load_config
from graphrag.config.models.graph_rag_config import GraphRagConfig

from tests.unit.config.utils import (
    DEFAULT_COMPLETION_MODELS,
    DEFAULT_EMBEDDING_MODELS,
    FAKE_API_KEY,
    assert_graphrag_configs,
    get_default_graphrag_config,
)


def test_default_config() -> None:
    expected = get_default_graphrag_config()
    actual = GraphRagConfig(
        completion_models=DEFAULT_COMPLETION_MODELS,  # type: ignore
        embedding_models=DEFAULT_EMBEDDING_MODELS,  # type: ignore
    )
    assert_graphrag_configs(actual, expected)


@mock.patch.dict(os.environ, {"CUSTOM_API_KEY": FAKE_API_KEY}, clear=True)
def test_load_minimal_config() -> None:
    cwd = Path.cwd()
    root_dir = (Path(__file__).parent / "fixtures" / "minimal_config").resolve()
    os.chdir(root_dir)
    expected = get_default_graphrag_config()

    actual = load_config(
        root_dir=root_dir,
    )
    assert_graphrag_configs(actual, expected)
    # Need to reset cwd after test
    os.chdir(cwd)


@mock.patch.dict(os.environ, {"CUSTOM_API_KEY": FAKE_API_KEY}, clear=True)
def test_load_config_with_cli_overrides() -> None:
    cwd = Path.cwd()
    root_dir = (Path(__file__).parent / "fixtures" / "minimal_config").resolve()
    os.chdir(root_dir)
    output_dir = "some_output_dir"
    expected_output_base_dir = root_dir / output_dir
    expected = get_default_graphrag_config()
    expected.output_storage.base_dir = str(expected_output_base_dir)

    actual = load_config(
        root_dir=root_dir,
        cli_overrides={"output_storage": {"base_dir": output_dir}},
    )
    assert_graphrag_configs(actual, expected)
    # Need to reset cwd after test
    os.chdir(cwd)
