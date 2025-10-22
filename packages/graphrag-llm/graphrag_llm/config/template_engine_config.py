# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Template engine configuration."""

from pydantic import BaseModel, ConfigDict, Field

from graphrag_llm.config.types import (
    TemplateEngineType,
    TemplateManagerType,
)


class TemplateEngineConfig(BaseModel):
    """Configuration for the template engine."""

    model_config = ConfigDict(extra="allow")
    """Allow extra fields to support custom metrics implementations."""

    type: str = Field(
        default=TemplateEngineType.Jinja,
        description="The template engine to use. [jinja]",
    )

    template_manager: str = Field(
        default=TemplateManagerType.File,
        description="The template manager to use. [file, memory] (default: file)",
    )

    base_dir: str | None = Field(
        default=None,
        description="The base directory for file-based template managers.",
    )

    template_extension: str | None = Field(
        default=None,
        description="The file extension for locating templates in file-based template managers.",
    )

    encoding: str | None = Field(
        default=None,
        description="The file encoding for reading templates in file-based template managers.",
    )
