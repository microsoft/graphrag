# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import json
import unittest
from typing import Any

from graphrag.config import create_graphrag_config
from graphrag.index import PipelineConfig, create_pipeline_config


def assert_contains_default_config(
    test_case: unittest.TestCase,
    config: Any,
    check_input=True,
    check_storage=True,
    check_reporting=True,
    check_cache=True,
    check_workflows=True,
):
    """Asserts that the config contains the default config."""
    assert config is not None
    assert isinstance(config, PipelineConfig)

    checked_config = json.loads(
        config.model_dump_json(exclude_defaults=True, exclude_unset=True)
    )

    actual_default_config = json.loads(
        create_pipeline_config(create_graphrag_config()).model_dump_json(
            exclude_defaults=True, exclude_unset=True
        )
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
