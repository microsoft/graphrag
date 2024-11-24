# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'PipelineConfig' model."""

from __future__ import annotations

from devtools import pformat
from pydantic import BaseModel
from pydantic import Field as pydantic_Field

from graphrag.index.config.cache import PipelineCacheConfigTypes
from graphrag.index.config.input import PipelineInputConfigTypes
from graphrag.index.config.reporting import PipelineReportingConfigTypes
from graphrag.index.config.storage import PipelineStorageConfigTypes
from graphrag.index.config.workflow import PipelineWorkflowReference


class PipelineConfig(BaseModel):
    """Represent the configuration for a pipeline."""

    def __repr__(self) -> str:
        """Get a string representation."""
        return pformat(self, highlight=False)

    def __str__(self):
        """Get a string representation."""
        return str(self.model_dump_json(indent=4))

    extends: list[str] | str | None = pydantic_Field(
        description="Extends another pipeline configuration", default=None
    )
    """Extends another pipeline configuration"""

    input: PipelineInputConfigTypes | None = pydantic_Field(
        default=None, discriminator="file_type"
    )
    """The input configuration for the pipeline."""

    reporting: PipelineReportingConfigTypes | None = pydantic_Field(
        default=None, discriminator="type"
    )
    """The reporting configuration for the pipeline."""

    storage: PipelineStorageConfigTypes | None = pydantic_Field(
        default=None, discriminator="type"
    )
    """The storage configuration for the pipeline."""

    update_index_storage: PipelineStorageConfigTypes | None = pydantic_Field(
        default=None, discriminator="type"
    )
    """The storage configuration for the updated index."""

    cache: PipelineCacheConfigTypes | None = pydantic_Field(
        default=None, discriminator="type"
    )
    """The cache configuration for the pipeline."""

    root_dir: str | None = pydantic_Field(
        description="The root directory for the pipeline. All other paths will be based on this root_dir.",
        default=None,
    )
    """The root directory for the pipeline."""

    workflows: list[PipelineWorkflowReference] = pydantic_Field(
        description="The workflows for the pipeline.", default_factory=list
    )
    """The workflows for the pipeline."""
