#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""Parameterization settings for the default configuration, loaded from environment variables."""


from environs import Env

from graphrag.index.default_config.parameters.defaults import (
    DEFAULT_NODE2VEC_IS_ENABLED,
    DEFAULT_NODE2VEC_ITERATIONS,
    DEFAULT_NODE2VEC_NUM_WALKS,
    DEFAULT_NODE2VEC_RANDOM_SEED,
    DEFAULT_NODE2VEC_WALK_LENGTH,
    DEFAULT_NODE2VEC_WINDOW_SIZE,
)
from graphrag.index.default_config.parameters.models import (
    EmbedGraphConfigModel,
)
from graphrag.index.verbs.graph.embed import EmbedGraphStrategyType

from .config_section import ConfigSection


class EmbedGraphConfigSection(ConfigSection):
    """The default configuration section for Node2Vec, loaded from environment variables."""

    _values: EmbedGraphConfigModel

    def __init__(self, values: EmbedGraphConfigModel, env: Env):
        """Create a new instance of the parameters class."""
        super().__init__(env)
        self._values = values

    @property
    def is_enabled(self) -> bool:
        """A flag indicating whether to enable node2vec."""
        return self.replace(self._values.is_enabled, DEFAULT_NODE2VEC_IS_ENABLED)

    @property
    def num_walks(self) -> int:
        """The node2vec number of walks."""
        return self.replace(self._values.num_walks, DEFAULT_NODE2VEC_NUM_WALKS)

    @property
    def walk_length(self) -> int:
        """The node2vec walk length."""
        return self.replace(self._values.walk_length, DEFAULT_NODE2VEC_WALK_LENGTH)

    @property
    def window_size(self) -> int:
        """The node2vec window size."""
        return self.replace(self._values.window_size, DEFAULT_NODE2VEC_WINDOW_SIZE)

    @property
    def iterations(self) -> int:
        """The node2vec iterations."""
        return self.replace(self._values.iterations, DEFAULT_NODE2VEC_ITERATIONS)

    @property
    def random_seed(self) -> int:
        """The node2vec random seed."""
        return self.replace(self._values.random_seed, DEFAULT_NODE2VEC_RANDOM_SEED)

    @property
    def strategy(self) -> dict | None:
        """The graph embedding strategy override."""
        return self.replace_dict(self._values.strategy) or {
            "type": EmbedGraphStrategyType.node2vec,
            "num_walks": self.num_walks,
            "walk_length": self.walk_length,
            "window_size": self.window_size,
            "iterations": self.iterations,
            "random_seed": self.iterations,
        }

    def to_dict(self) -> dict:
        """Convert the configuration to a dictionary."""
        return {
            "is_enabled": self.is_enabled,
            "num_walks": self.num_walks,
            "walk_length": self.walk_length,
            "window_size": self.window_size,
            "iterations": self.iterations,
            "random_seed": self.random_seed,
            "strategy": self._values.strategy,
        }
