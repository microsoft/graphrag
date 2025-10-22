# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Metrics configuration."""

import logging
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from graphrag_llm.config.types import (
    MetricsProcessorType,
    MetricsStoreType,
    MetricsWriterType,
)


class MetricsConfig(BaseModel):
    """Configuration for metrics."""

    model_config = ConfigDict(extra="allow")
    """Allow extra fields to support custom metrics implementations."""

    type: str = Field(
        default=MetricsProcessorType.Default,
        description="MetricsProcessor implementation to use.",
    )

    store: str = Field(
        default=MetricsStoreType.Memory,
        description="MetricsStore implementation to use. [memory] (default: memory).",
    )

    writer: str | None = Field(
        default=MetricsWriterType.Log,
        description="MetricsWriter implementation to use. [log, file] (default: log).",
    )

    log_level: int | None = Field(
        default=logging.INFO,
        description="Log level to use when using the 'Log' metrics writer. (default: INFO)",
    )

    base_dir: str | None = Field(
        default=str(Path.cwd() / "metrics"),
        description="Base directory for file-based metrics writer. (default: ./metrics)",
    )
