#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""Parameterization settings for the default configuration, loaded from environment variables."""
from environs import Env

from graphrag.index.default_config.parameters.defaults import (
    DEFAULT_CHUNK_GROUP_BY_COLUMNS,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
)
from graphrag.index.default_config.parameters.models import (
    ChunkingConfigModel,
)
from graphrag.index.verbs.text.chunk import ChunkStrategyType

from .config_section import ConfigSection


class ChunkingConfigSection(ConfigSection):
    """The default configuration section for Chunking, loaded from environment variables."""

    _values: ChunkingConfigModel
    _encoding_model: str

    def __init__(self, values: ChunkingConfigModel, encoding_model: str, env: Env):
        """Create a new instance of the parameters class."""
        super().__init__(env)
        self._values = values
        self._encoding_model = encoding_model

    @property
    def size(self) -> int:
        """The chunk size to use."""
        return self.replace(self._values.size, DEFAULT_CHUNK_SIZE)

    @property
    def overlap(self) -> int:
        """The chunk overlap to use."""
        return self.replace(self._values.overlap, DEFAULT_CHUNK_OVERLAP)

    @property
    def group_by_columns(self) -> list[str]:
        """The chunk by columns to use."""
        return self.replace(
            self._values.group_by_columns, DEFAULT_CHUNK_GROUP_BY_COLUMNS
        )

    @property
    def strategy(self) -> dict | None:
        """The chunk strategy to use, overriding the default tokenization strategy."""
        return self.replace_dict(self._values.strategy) or {
            "type": ChunkStrategyType.tokens,
            "chunk_size": self.size,
            "chunk_overlap": self.overlap,
            "encoding_name": self._encoding_model,
        }

    def to_dict(self) -> dict:
        """Convert the configuration to a dictionary."""
        return {
            "size": self.size,
            "overlap": self.overlap,
            "group_by_columns": self.group_by_columns,
            "strategy": self._values.strategy,
        }
