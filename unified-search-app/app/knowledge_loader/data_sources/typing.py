# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Data sources typing module."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

import pandas as pd

from graphrag.config.models.graph_rag_config import GraphRagConfig


class WriteMode(Enum):
    """An enum for the write modes of a datasource."""

    # Overwrite means all the data in the table will be replaced with the new data.
    Overwrite = 1

    # Append means the new data will be appended to the existing data in the table.
    Append = 2


class Datasource(ABC):
    """An interface for a datasource, which is a function that takes a table name and returns a DataFrame or None."""

    def __call__(self, table: str, columns: list[str] | None) -> pd.DataFrame:
        """Call method definition."""
        raise NotImplementedError

    @abstractmethod
    def read(
        self,
        table: str,
        throw_on_missing: bool = False,
        columns: list[str] | None = None,
    ) -> pd.DataFrame:
        """Read method definition."""
        raise NotImplementedError

    @abstractmethod
    def read_settings(self, file: str) -> GraphRagConfig | None:
        """Read settings method definition."""
        raise NotImplementedError

    def write(
        self, table: str, df: pd.DataFrame, mode: WriteMode | None = None
    ) -> None:
        """Write method definition."""
        raise NotImplementedError

    def has_table(self, table: str) -> bool:
        """Check if table exists method definition."""
        raise NotImplementedError


@dataclass
class VectorIndexConfig:
    """VectorIndexConfig class definition."""

    index_name: str
    embeddings_file: str
    content_file: str | None = None


@dataclass
class DatasetConfig:
    """DatasetConfig class definition."""

    key: str
    path: str
    name: str
    description: str
    community_level: int
