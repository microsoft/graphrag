# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

import os
from pathlib import Path
from unittest import mock

from graphrag.config.load_config import load_config
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag_llm.config import AuthMethod

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


def test_load_provider_managed_models(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GRAPHRAG_API_KEY", "unrelated-key")
    (tmp_path / "settings.yaml").write_text(
        """completion_models:
  default_completion_model:
    model_provider: github_copilot
    model: gpt-4o
    auth_method: provider
embedding_models:
  default_embedding_model:
    model_provider: github_copilot
    model: text-embedding-3-small
    auth_method: provider
""",
        encoding="utf-8",
    )
    config = load_config(tmp_path)
    completion = config.completion_models["default_completion_model"]
    embedding = config.embedding_models["default_embedding_model"]
    assert completion.auth_method == AuthMethod.Provider
    assert embedding.auth_method == AuthMethod.Provider
    assert completion.api_key is None
    assert embedding.api_key is None


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
