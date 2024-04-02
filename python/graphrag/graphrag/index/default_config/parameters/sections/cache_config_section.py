# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration, loaded from environment variables."""

from environs import Env

from graphrag.index.config import PipelineCacheType
from graphrag.index.default_config.parameters.defaults import (
    DEFAULT_CACHE_BASE_DIR,
    DEFAULT_CACHE_TYPE,
)
from graphrag.index.default_config.parameters.models import (
    CacheConfigModel,
)

from .config_section import ConfigSection


class CacheConfigSection(ConfigSection):
    """The default configuration section for Cache, loaded from environment variables."""

    _values: CacheConfigModel

    def __init__(self, values: CacheConfigModel, env: Env):
        """Create a new instance of the parameters class."""
        super().__init__(env)
        self._values = values

    @property
    def type(self) -> PipelineCacheType:
        """The cache type to use."""
        result = self.replace(str(self._values.type))
        return PipelineCacheType(result) if result else DEFAULT_CACHE_TYPE

    @property
    def connection_string(self) -> str:
        """The cache connection string to use."""
        return self.replace(self._values.connection_string)

    @property
    def container_name(self) -> str:
        """The cache container name to use."""
        return self.replace(self._values.container_name)

    @property
    def base_dir(self) -> str:
        """The base directory for the cache."""
        return self.replace(self._values.base_dir, DEFAULT_CACHE_BASE_DIR)

    def to_dict(self) -> dict:
        """Convert the configuration to a dictionary."""
        return {
            "type": self.type,
            "connection_string": self.connection_string,
            "container_name": self.container_name,
            "base_dir": self.base_dir,
        }
