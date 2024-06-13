# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'PipelineInputConfig', 'PipelineCSVInputConfig' and 'PipelineTextInputConfig' models."""

from __future__ import annotations

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel
from pydantic import Field as pydantic_Field

from graphrag.config.enums import InputFileType, InputType

from .workflow import PipelineWorkflowStep

T = TypeVar("T")


class PipelineInputConfig(BaseModel, Generic[T]):
    """Represent the configuration for an input."""

    file_type: T
    """The file type of input."""

    type: InputType | None = pydantic_Field(
        description="The input type to use.",
        default=None,
    )
    """The input type to use."""

    connection_string: str | None = pydantic_Field(
        description="The blob cache connection string for the input files.",
        default=None,
    )
    """The blob cache connection string for the input files."""

    storage_account_blob_url: str | None = pydantic_Field(
        description="The storage account blob url for the input files.", default=None
    )
    """The storage account blob url for the input files."""

    container_name: str | None = pydantic_Field(
        description="The container name for input files.", default=None
    )
    """The container name for the input files."""

    base_dir: str | None = pydantic_Field(
        description="The base directory for the input files.", default=None
    )
    """The base directory for the input files."""

    file_pattern: str = pydantic_Field(
        description="The regex file pattern for the input files."
    )
    """The regex file pattern for the input files."""

    file_filter: dict[str, str] | None = pydantic_Field(
        description="The optional file filter for the input files.", default=None
    )
    """The optional file filter for the input files."""

    post_process: list[PipelineWorkflowStep] | None = pydantic_Field(
        description="The post processing steps for the input.", default=None
    )
    """The post processing steps for the input."""

    encoding: str | None = pydantic_Field(
        description="The encoding for the input files.", default=None
    )
    """The encoding for the input files."""


class PipelineCSVInputConfig(PipelineInputConfig[Literal[InputFileType.csv]]):
    """Represent the configuration for a CSV input."""

    file_type: Literal[InputFileType.csv] = InputFileType.csv

    source_column: str | None = pydantic_Field(
        description="The column to use as the source of the document.", default=None
    )
    """The column to use as the source of the document."""

    timestamp_column: str | None = pydantic_Field(
        description="The column to use as the timestamp of the document.", default=None
    )
    """The column to use as the timestamp of the document."""

    timestamp_format: str | None = pydantic_Field(
        description="The format of the timestamp column, so it can be parsed correctly.",
        default=None,
    )
    """The format of the timestamp column, so it can be parsed correctly."""

    text_column: str | None = pydantic_Field(
        description="The column to use as the text of the document.", default=None
    )
    """The column to use as the text of the document."""

    title_column: str | None = pydantic_Field(
        description="The column to use as the title of the document.", default=None
    )
    """The column to use as the title of the document."""


class PipelineTextInputConfig(PipelineInputConfig[Literal[InputFileType.text]]):
    """Represent the configuration for a text input."""

    file_type: Literal[InputFileType.text] = InputFileType.text

    # Text Specific
    title_text_length: int | None = pydantic_Field(
        description="Number of characters to use from the text as the title.",
        default=None,
    )
    """Number of characters to use from the text as the title."""


PipelineInputConfigTypes = PipelineCSVInputConfig | PipelineTextInputConfig
"""Represent the types of inputs that can be used in a pipeline."""
