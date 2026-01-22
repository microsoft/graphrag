# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Template engine configuration."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

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

    def _validate_file_template_manager_config(self) -> None:
        """Validate parameters for file-based template managers."""
        if self.base_dir is not None and self.base_dir.strip() == "":
            msg = "base_dir must be specified for file-based template managers."
            raise ValueError(msg)

        if (
            self.template_extension is not None
            and self.template_extension.strip() == ""
        ):
            msg = "template_extension cannot be an empty string for file-based template managers."
            raise ValueError(msg)

        if (
            self.template_extension is not None
            and not self.template_extension.startswith(".")
        ):
            self.template_extension = f".{self.template_extension}"

    @model_validator(mode="after")
    def _validate_model(self):
        """Validate the template engine configuration based on its type."""
        if self.template_manager == TemplateManagerType.File:
            self._validate_file_template_manager_config()
        return self
