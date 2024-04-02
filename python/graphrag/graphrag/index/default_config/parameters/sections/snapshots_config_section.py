# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration, loaded from environment variables."""

from environs import Env

from graphrag.index.default_config.parameters.defaults import (
    DEFAULT_SNAPSHOTS_GRAPHML,
    DEFAULT_SNAPSHOTS_RAW_ENTITIES,
    DEFAULT_SNAPSHOTS_TOP_LEVEL_NODES,
)
from graphrag.index.default_config.parameters.models import (
    SnapshotsConfigModel,
)

from .config_section import ConfigSection


class SnapshotsConfigSection(ConfigSection):
    """The default configuration section for Snapshots, loaded from environment variables."""

    _values: SnapshotsConfigModel

    def __init__(self, values: SnapshotsConfigModel, env: Env):
        """Create a new instance of the parameters class."""
        super().__init__(env)
        self._values = values

    @property
    def graphml(self) -> bool:
        """A flag indicating whether to take snapshots of GraphML."""
        return self.replace(self._values.graphml, DEFAULT_SNAPSHOTS_GRAPHML)

    @property
    def raw_entities(self) -> bool:
        """A flag indicating whether to take snapshots of raw_entities."""
        return self.replace(self._values.raw_entities, DEFAULT_SNAPSHOTS_RAW_ENTITIES)

    @property
    def top_level_nodes(self) -> bool:
        """A flag indicating whether to take snapshots of top level nodes."""
        return self.replace(
            self._values.top_level_nodes, DEFAULT_SNAPSHOTS_TOP_LEVEL_NODES
        )

    def to_dict(self) -> dict:
        """Convert the configuration to a dictionary."""
        return {
            "graphml": self.graphml,
            "raw_entities": self.raw_entities,
            "top_level_nodes": self.top_level_nodes,
        }
