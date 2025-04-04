"""
Copyright (c) Microsoft Corporation. All rights reserved.
"""

from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import Optional

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
        raise NotImplementedError()

    def read(
        self,
        table: str,
        throw_on_missing: bool = False,
        columns: Optional[list[str]] = None,
    ) -> pd.DataFrame: ...

    def read_settings(self, file: str) -> GraphRagConfig | None: ...

    def write(
        self, table: str, df: pd.DataFrame, mode: WriteMode | None = None
    ) -> None: ...

    def has_table(self, table: str) -> bool: ...


@dataclass
class VectorIndexConfig:
    index_name: str
    embeddings_file: str
    content_file: Optional[str] | None = None


@dataclass
class DatasetConfig:
    key: str
    path: str
    name: str
    description: str
    community_level: int
