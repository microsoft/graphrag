# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT Licenses
import json
import os
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from graphrag.config import create_graphrag_config
from graphrag.index import (
    PipelineConfig,
    create_pipeline_config,
    load_pipeline_config,
)

current_dir = os.path.dirname(__file__)


class TestLoadPipelineConfig(unittest.TestCase):
    @mock.patch.dict(os.environ, {"GRAPHRAG_API_KEY": "test"}, clear=True)
    def test_config_passed_in_returns_config(self):
        config = PipelineConfig()
        result = load_pipeline_config(config)
        assert result == config

    @mock.patch.dict(os.environ, {"GRAPHRAG_API_KEY": "test"}, clear=True)
    def test_loading_default_config_returns_config(self):
        result = load_pipeline_config("default")
        self.assert_is_default_config(result)

    @mock.patch.dict(os.environ, {"GRAPHRAG_API_KEY": "test"}, clear=True)
    def test_loading_default_config_with_input_overridden(self):
        config = load_pipeline_config(
            str(Path(current_dir) / "default_config_with_overridden_input.yml")
        )

        # Check that the config is merged
        # but skip checking the input
        self.assert_is_default_config(config, check_input=False)

        if config.input is None:
            msg = "Input should not be none"
            raise Exception(msg)

        # Check that the input is merged
        assert config.input.file_pattern == "test.txt"
        assert config.input.file_type == "text"
        assert config.input.base_dir == "/some/overridden/dir"

    @mock.patch.dict(os.environ, {"GRAPHRAG_API_KEY": "test"}, clear=True)
    def test_loading_default_config_with_workflows_overridden(self):
        config = load_pipeline_config(
            str(Path(current_dir) / "default_config_with_overridden_workflows.yml")
        )

        # Check that the config is merged
        # but skip checking the input
        self.assert_is_default_config(config, check_workflows=False)

        # Make sure the workflows are overridden
        assert len(config.workflows) == 1
        assert config.workflows[0].name == "TEST_WORKFLOW"
        assert config.workflows[0].steps is not None
        assert len(config.workflows[0].steps) == 1  # type: ignore
        assert config.workflows[0].steps[0]["verb"] == "TEST_VERB"  # type: ignore

    @mock.patch.dict(os.environ, {"GRAPHRAG_API_KEY": "test"}, clear=True)
    def assert_is_default_config(
        self,
        config: Any,
        check_input=True,
        check_storage=True,
        check_reporting=True,
        check_cache=True,
        check_workflows=True,
    ):
        assert config is not None
        assert isinstance(config, PipelineConfig)

        checked_config = json.loads(
            config.model_dump_json(exclude_defaults=True, exclude_unset=True)
        )

        actual_default_config = json.loads(
            create_pipeline_config(
                create_graphrag_config(root_dir=".")
            ).model_dump_json(exclude_defaults=True, exclude_unset=True)
        )
        props_to_ignore = ["root_dir", "extends"]

        # Make sure there is some sort of workflows
        if not check_workflows:
            props_to_ignore.append("workflows")

        # Make sure it tries to load some sort of input
        if not check_input:
            props_to_ignore.append("input")

        # Make sure it tries to load some sort of storage
        if not check_storage:
            props_to_ignore.append("storage")

        # Make sure it tries to load some sort of reporting
        if not check_reporting:
            props_to_ignore.append("reporting")

        # Make sure it tries to load some sort of cache
        if not check_cache:
            props_to_ignore.append("cache")

        for prop in props_to_ignore:
            checked_config.pop(prop, None)
            actual_default_config.pop(prop, None)

        assert actual_default_config == actual_default_config | checked_config

    def setUp(self) -> None:
        os.environ["GRAPHRAG_OPENAI_API_KEY"] = "test"
        os.environ["GRAPHRAG_OPENAI_EMBEDDING_API_KEY"] = "test"
        return super().setUp()
