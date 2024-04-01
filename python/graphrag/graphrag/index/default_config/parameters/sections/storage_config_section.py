#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""Parameterization settings for the default configuration, loaded from environment variables."""


from environs import Env

from graphrag.index.config import PipelineStorageType
from graphrag.index.default_config.parameters.defaults import DEFAULT_STORAGE_TYPE
from graphrag.index.default_config.parameters.models import (
    StorageConfigModel,
)

from .config_section import ConfigSection


class StorageConfigSection(ConfigSection):
    """The default configuration section for Storage, loaded from environment variables."""

    _values: StorageConfigModel

    def __init__(self, values: StorageConfigModel, env: Env):
        """Create a new instance of the parameters class."""
        super().__init__(env)
        self._values = values

    @property
    def type(self) -> PipelineStorageType:
        """The storage type to use."""
        return self.replace(self._values.type, DEFAULT_STORAGE_TYPE)

    @property
    def connection_string(self) -> str:
        """The storage connection string to use."""
        return self.replace(self._values.connection_string)

    @property
    def container_name(self) -> str:
        """The storage container name to use."""
        return self.replace(self._values.container_name)

    @property
    def base_dir(self) -> str:
        """The base directory for the storage."""
        return self.replace(self._values.base_dir)

    def to_dict(self) -> dict:
        """Convert the configuration to a dictionary."""
        return {
            "type": self.type,
            "connection_string": self.connection_string,
            "container_name": self.container_name,
            "base_dir": self.base_dir,
        }
