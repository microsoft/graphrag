# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

from graphrag.config.defaults import graphrag_config_defaults
from graphrag.config.enums import OutputType


class OutputConfig(BaseModel):
    """The default configuration section for Output."""

    type: OutputType = Field(
        description="The output type to use.",
        default=graphrag_config_defaults.output.type,
    )
    base_dir: str = Field(
        description="The base directory for the output.",
        default=graphrag_config_defaults.output.base_dir,
    )
    connection_string: str | None = Field(
        description="The storage connection string to use.",
        default=graphrag_config_defaults.output.connection_string,
    )
    container_name: str | None = Field(
        description="The storage container name to use.",
        default=graphrag_config_defaults.output.container_name,
    )
    storage_account_blob_url: str | None = Field(
        description="The storage account blob url to use.",
        default=graphrag_config_defaults.output.storage_account_blob_url,
    )
    cosmosdb_account_url: str | None = Field(
        description="The cosmosdb account url to use.",
        default=graphrag_config_defaults.output.cosmosdb_account_url,
    )
    database_name: str | None = Field(
        description="The database name to use for SQL Server.",
        default=graphrag_config_defaults.output.database_name,
    )
    database_server_name: str | None = Field(
        description="The database server name to use for SQL Server.",
        default=graphrag_config_defaults.output.database_server_name,
    )
    autogenerate_tables: bool | None = Field(
        description="Whether to automatically generate tables in SQL Server.",
        default=graphrag_config_defaults.output.autogenerate_tables,
    )
    client_id: str | None = Field(
        description="The client ID for a User-Assigned Managed Identity (SQL Server).",
        default=graphrag_config_defaults.output.client_id,
    )
