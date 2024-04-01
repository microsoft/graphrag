#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""Parameterization settings for the default configuration, loaded from environment variables."""
from environs import Env

from graphrag.index.default_config.parameters.defaults import (
    DEFAULT_MAX_CLUSTER_SIZE,
)
from graphrag.index.default_config.parameters.models import (
    ClusterGraphConfigModel,
)
from graphrag.index.verbs.graph.clustering import GraphCommunityStrategyType

from .config_section import ConfigSection


class ClusterGraphConfigSection(ConfigSection):
    """The default configuration section for ClusterGraph, loaded from environment variables."""

    _values: ClusterGraphConfigModel

    def __init__(self, values: ClusterGraphConfigModel, env: Env):
        """Create a new instance of the parameters class."""
        super().__init__(env)
        self._values = values

    @property
    def max_cluster_size(self) -> int:
        """The maximum cluster size to use."""
        return self.replace(self._values.max_cluster_size, DEFAULT_MAX_CLUSTER_SIZE)

    @property
    def strategy(self) -> dict | None:
        """The cluster strategy to use."""
        return self.replace_dict(self._values.strategy) or {
            "type": GraphCommunityStrategyType.leiden,
            "max_cluster_size": self.max_cluster_size,
        }

    def to_dict(self) -> dict:
        """Convert the configuration to a dictionary."""
        return {
            "max_cluster_size": self.max_cluster_size,
            "strategy": self._values.strategy,
        }
