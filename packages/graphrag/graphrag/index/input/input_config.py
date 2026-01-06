# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from graphrag_storage import StorageConfig
from pydantic import BaseModel, ConfigDict, Field

import graphrag.config.defaults as defs
from graphrag.config.defaults import graphrag_config_defaults


class InputConfig(BaseModel):
    """The default configuration section for Input."""

    model_config = ConfigDict(extra="allow")
    """Allow extra fields to support custom reader implementations."""

    storage: StorageConfig = Field(
        description="The storage configuration to use for reading input documents.",
        default=StorageConfig(
            base_dir=graphrag_config_defaults.input.storage.base_dir,
        ),
    )
    file_type: str = Field(
        description="The input file type to use.",
        default=graphrag_config_defaults.input.file_type,
    )
    encoding: str = Field(
        description="The input file encoding to use.",
        default=defs.graphrag_config_defaults.input.encoding,
    )
    file_pattern: str = Field(
        description="The input file pattern to use.",
        default=graphrag_config_defaults.input.file_pattern,
    )
    text_column: str | None = Field(
        description="The input text column to use.",
        default=graphrag_config_defaults.input.text_column,
    )
    title_column: str | None = Field(
        description="The input title column to use.",
        default=graphrag_config_defaults.input.title_column,
    )
    metadata: list[str] | None = Field(
        description="The document attribute columns to use.",
        default=graphrag_config_defaults.input.metadata,
    )
