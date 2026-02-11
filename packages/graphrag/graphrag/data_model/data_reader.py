# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A DataReader that loads typed dataframes from a TableProvider."""

import pandas as pd
from graphrag_storage.tables import TableProvider

from graphrag.data_model.dfs import (
    communities_typed,
    community_reports_typed,
    covariates_typed,
    documents_typed,
    entities_typed,
    relationships_typed,
    text_units_typed,
)


class DataReader:
    """Reads dataframes from a TableProvider and applies correct column types.

    When loading from weakly-typed formats like CSV, list columns are stored as
    plain strings. This class wraps a TableProvider, loading each table and
    converting columns to their expected types before returning.
    """

    def __init__(self, table_provider: TableProvider) -> None:
        """Initialize a DataReader with the given TableProvider.

        Args
        ----
            table_provider: TableProvider
                The table provider to load dataframes from.
        """
        self._table_provider = table_provider

    async def entities(self) -> pd.DataFrame:
        """Load and return the entities dataframe with correct types."""
        df = await self._table_provider.read_dataframe("entities")
        return entities_typed(df)

    async def relationships(self) -> pd.DataFrame:
        """Load and return the relationships dataframe with correct types."""
        df = await self._table_provider.read_dataframe("relationships")
        return relationships_typed(df)

    async def communities(self) -> pd.DataFrame:
        """Load and return the communities dataframe with correct types."""
        df = await self._table_provider.read_dataframe("communities")
        return communities_typed(df)

    async def community_reports(self) -> pd.DataFrame:
        """Load and return the community reports dataframe with correct types."""
        df = await self._table_provider.read_dataframe("community_reports")
        return community_reports_typed(df)

    async def covariates(self) -> pd.DataFrame:
        """Load and return the covariates dataframe with correct types."""
        df = await self._table_provider.read_dataframe("covariates")
        return covariates_typed(df)

    async def text_units(self) -> pd.DataFrame:
        """Load and return the text units dataframe with correct types."""
        df = await self._table_provider.read_dataframe("text_units")
        return text_units_typed(df)

    async def documents(self) -> pd.DataFrame:
        """Load and return the documents dataframe with correct types."""
        df = await self._table_provider.read_dataframe("documents")
        return documents_typed(df)
