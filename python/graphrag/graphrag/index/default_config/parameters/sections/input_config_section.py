# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration, loaded from environment variables."""

from environs import Env

from graphrag.index.config import PipelineInputStorageType, PipelineInputType
from graphrag.index.default_config.parameters.defaults import (
    DEFAULT_INPUT_BASE_DIR,
    DEFAULT_INPUT_CSV_PATTERN,
    DEFAULT_INPUT_FILE_ENCODING,
    DEFAULT_INPUT_STORAGE_TYPE,
    DEFAULT_INPUT_TEXT_COLUMN,
    DEFAULT_INPUT_TEXT_PATTERN,
    DEFAULT_INPUT_TYPE,
)
from graphrag.index.default_config.parameters.models import (
    InputConfigModel,
)

from .config_section import ConfigSection


class InputConfigSection(ConfigSection):
    """The default configuration section for Input, loaded from environment variables."""

    _values: InputConfigModel

    def __init__(self, values: InputConfigModel, env: Env):
        """Create a new instance of the parameters class."""
        super().__init__(env)
        self._values = values

    @property
    def type(self) -> PipelineInputType:
        """The input type to use."""
        return self.replace(self._values.type, DEFAULT_INPUT_TYPE)

    @property
    def storage_type(self) -> PipelineInputStorageType:
        """The input storage type to use."""
        return self.replace(self._values.storage_type, DEFAULT_INPUT_STORAGE_TYPE)

    @property
    def connection_string(self) -> str | None:
        """The azure blob storage connection string to use."""
        return self.replace(self._values.connection_string)

    @property
    def container_name(self) -> str | None:
        """The azure blob storage container name to use."""
        return self.replace(self._values.container_name)

    @property
    def base_dir(self) -> str:
        """The input base directory to use."""
        return self.replace(self._values.base_dir, DEFAULT_INPUT_BASE_DIR)

    @property
    def file_encoding(self) -> str:
        """The input file encoding to use."""
        return self.replace(self._values.file_encoding, DEFAULT_INPUT_FILE_ENCODING)

    @property
    def file_pattern(self) -> str:
        """The input file pattern to use."""
        if self.type == "text":
            return self.replace(self._values.file_pattern, DEFAULT_INPUT_TEXT_PATTERN)

        return self.replace(self._values.file_pattern, DEFAULT_INPUT_CSV_PATTERN)

    @property
    def source_column(self) -> str | None:
        """The input source column to use."""
        return self.replace(self._values.source_column)

    @property
    def timestamp_column(self) -> str | None:
        """The input timestamp column to use."""
        return self.replace(self._values.timestamp_column)

    @property
    def timestamp_format(self) -> str | None:
        """The input timestamp format to use."""
        return self.replace(self._values.timestamp_format)

    @property
    def text_column(self) -> str:
        """The input text column to use."""
        return self.replace(self._values.text_column, DEFAULT_INPUT_TEXT_COLUMN)

    @property
    def title_column(self) -> str | None:
        """The input title column to use."""
        return self.replace(self._values.title_column)

    @property
    def document_attribute_columns(self) -> list[str]:
        """The document attribute columns to use."""
        return self.replace(self._values.document_attribute_columns, [])

    def to_dict(self) -> dict:
        """Convert the configuration to a dictionary."""
        return {
            "type": self.type,
            "storage_type": self.storage_type,
            "connection_string": self.connection_string,
            "container_name": self.container_name,
            "base_dir": self.base_dir,
            "file_encoding": self.file_encoding,
            "file_pattern": self.file_pattern,
            "source_column": self.source_column,
            "timestamp_column": self.timestamp_column,
            "timestamp_format": self.timestamp_format,
            "text_column": self.text_column,
            "title_column": self.title_column,
            "document_attribute_columns": self.document_attribute_columns,
        }
