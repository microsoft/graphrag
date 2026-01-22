# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Test metrics configuration loading."""

import pytest
from graphrag_llm.config import (
    TemplateEngineConfig,
    TemplateEngineType,
    TemplateManagerType,
)


def test_template_engine_config_validation() -> None:
    """Test that missing required parameters raise validation errors."""

    with pytest.raises(
        ValueError,
        match="base_dir must be specified for file-based template managers\\.",
    ):
        _ = TemplateEngineConfig(
            type=TemplateEngineType.Jinja,
            template_manager=TemplateManagerType.File,
            base_dir="   ",
        )

    with pytest.raises(
        ValueError,
        match="template_extension cannot be an empty string for file-based template managers\\.",
    ):
        _ = TemplateEngineConfig(
            type=TemplateEngineType.Jinja,
            template_manager=TemplateManagerType.File,
            base_dir="./templates",
            template_extension="   ",
        )

    # passes validation
    _ = TemplateEngineConfig(
        type=TemplateEngineType.Jinja,
        template_manager=TemplateManagerType.File,
        base_dir="./templates",
        template_extension=".jinja",
    )
