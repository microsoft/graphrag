# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Test metrics configuration loading."""

import pytest
from graphrag_llm.config import (
    MetricsConfig,
    MetricsWriterType,
)


def test_file_metrics_writer_validation() -> None:
    """Test that missing required parameters raise validation errors."""

    with pytest.raises(
        ValueError,
        match="base_dir must be specified for file-based metrics writer\\.",
    ):
        _ = MetricsConfig(
            writer=MetricsWriterType.File,
            base_dir="   ",
        )

    # passes validation
    _ = MetricsConfig(
        writer=MetricsWriterType.File,
        base_dir="./metrics",
    )
