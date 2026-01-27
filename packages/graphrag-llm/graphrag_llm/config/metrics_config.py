# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Metrics configuration."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
        default=None,
        description="Log level to use when using the 'Log' metrics writer. (default: INFO)",
    )

    base_dir: str | None = Field(
        default=None,
        description="Base directory for file-based metrics writer. (default: ./metrics)",
    )

    def _validate_file_metrics_writer_config(self) -> None:
        """Validate parameters for file-based metrics writer."""
        if self.base_dir is not None and self.base_dir.strip() == "":
            msg = "base_dir must be specified for file-based metrics writer."
            raise ValueError(msg)

    @model_validator(mode="after")
    def _validate_model(self):
        """Validate the metrics configuration based on its writer type."""
        if self.writer == MetricsWriterType.File:
            self._validate_file_metrics_writer_config()
        return self
