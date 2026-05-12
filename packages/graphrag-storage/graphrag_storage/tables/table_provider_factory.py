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
            case TableType.CosmosDB:
                from graphrag_storage.tables.cosmos_table_provider import (
                    CosmosTableProvider,
                )

                register_table_provider(TableType.CosmosDB, CosmosTableProvider)
            case _:
                msg = f"TableProviderConfig.type '{table_type}' is not registered in the TableProviderFactory. Registered types: {', '.join(table_provider_factory.keys())}."
                raise ValueError(msg)

    if storage:
        config_model["storage"] = storage

    # For CosmosDB table providers, extract connection details from the
    # affiliated Storage instance so users only configure credentials once
    # (on output_storage).  Table-specific fields (container_name,
    # batch_size, legacy_container) stay on TableProviderConfig.
    if table_type == TableType.CosmosDB and storage is not None:
        from graphrag_storage.azure_cosmos_storage import AzureCosmosStorage

        if isinstance(storage, AzureCosmosStorage):
            config_model.setdefault(
                "connection_string",
                storage._connection_string,  # noqa: SLF001
            )
            config_model.setdefault(
                "account_url",
                storage._cosmosdb_account_url,  # noqa: SLF001
            )
            config_model.setdefault(
                "database_name",
                storage._database_name,  # noqa: SLF001
            )

    return table_provider_factory.create(table_type, config_model)
