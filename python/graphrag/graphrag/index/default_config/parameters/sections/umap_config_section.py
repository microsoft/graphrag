# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration, loaded from environment variables."""

from environs import Env

from graphrag.index.default_config.parameters.defaults import DEFAULT_UMAP_ENABLED
from graphrag.index.default_config.parameters.models import (
    UmapConfigModel,
)

from .config_section import ConfigSection


class UmapConfigSection(ConfigSection):
    """The default configuration section for Umap, loaded from environment variables."""

    _values: UmapConfigModel

    def __init__(self, values: UmapConfigModel, env: Env):
        """Create a new instance of the parameters class."""
        super().__init__(env)
        self._values = values

    @property
    def enabled(self) -> bool:
        """A flag indicating whether to enable UMAP."""
        return self.replace(self._values.enabled, DEFAULT_UMAP_ENABLED)

    def to_dict(self) -> dict:
        """Convert the configuration to a dictionary."""
        return {
            "enabled": self.enabled,
        }
