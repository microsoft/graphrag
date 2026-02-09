# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License


"""Storage factory implementation."""

from collections.abc import Callable

from graphrag_common.factory import Factory, ServiceScope

from graphrag_storage.storage import Storage
from graphrag_storage.tables.table_provider import TableProvider
from graphrag_storage.tables.table_provider_config import TableProviderConfig
from graphrag_storage.tables.table_type import TableType


class TableProviderFactory(Factory[TableProvider]):
    """A factory class for table storage implementations."""


table_provider_factory = TableProviderFactory()


def register_table_provider(
    table_type: str,
    table_initializer: Callable[..., TableProvider],
    scope: ServiceScope = "transient",
) -> None:
    """Register a custom storage implementation.

    Args
    ----
        - table_type: str
            The table type id to register.
        - table_initializer: Callable[..., TableProvider]
            The table initializer to register.
    """
    table_provider_factory.register(table_type, table_initializer, scope)


def create_table_provider(
    config: TableProviderConfig, storage: Storage | None = None
) -> TableProvider:
    """Create a table provider implementation based on the given configuration.

    Args
    ----
        - config: TableProviderConfig
            The table provider configuration to use.
        - storage: Storage | None
            The storage implementation to use for file-based TableProviders such as Parquet and CSV.

    Returns
    -------
        TableProvider
            The created table provider implementation.
    """
    config_model = config.model_dump()
    table_type = config.type

    if table_type not in table_provider_factory:
        match table_type:
            case TableType.Parquet:
                from graphrag_storage.tables.parquet_table_provider import (
                    ParquetTableProvider,
                )

                register_table_provider(TableType.Parquet, ParquetTableProvider)
            case TableType.CSV:
                from graphrag_storage.tables.csv_table_provider import (
                    CSVTableProvider,
                )

                register_table_provider(TableType.CSV, CSVTableProvider)
            case _:
                msg = f"TableProviderConfig.type '{table_type}' is not registered in the TableProviderFactory. Registered types: {', '.join(table_provider_factory.keys())}."
                raise ValueError(msg)

    if storage:
        config_model["storage"] = storage

    return table_provider_factory.create(table_type, config_model)
