# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from graphrag.config.defaults import graphrag_config_defaults
from graphrag.config.enums import StorageType


class StorageConfig(BaseModel):
    """The default configuration section for storage."""

    type: StorageType | str = Field(
        description="The storage type to use.",
        default=graphrag_config_defaults.storage.type,
    )
    base_dir: str = Field(
        description="The base directory for the output.",
        default=graphrag_config_defaults.storage.base_dir,
    )

    # Validate the base dir for multiple OS (use Path)
    # if not using a cloud storage type.
    @field_validator("base_dir", mode="before")
    @classmethod
    def validate_base_dir(cls, value, info):
        """Ensure that base_dir is a valid filesystem path when using local storage."""
        # info.data contains other field values, including 'type'
        if info.data.get("type") != StorageType.file:
            return value
        return str(Path(value))

    connection_string: str | None = Field(
        description="The storage connection string to use.",
        default=graphrag_config_defaults.storage.connection_string,
    )
    container_name: str | None = Field(
        description="The storage container name to use.",
        default=graphrag_config_defaults.storage.container_name,
    )
    storage_account_blob_url: str | None = Field(
        description="The storage account blob url to use.",
        default=graphrag_config_defaults.storage.storage_account_blob_url,
    )
    cosmosdb_account_url: str | None = Field(
        description="The cosmosdb account url to use.",
        default=graphrag_config_defaults.storage.cosmosdb_account_url,
    )

    ### PostgreSQL
    host: str = Field(
        description="PostgreSQL server host (for postgres type).",
        default="localhost"
    )
    port: int = Field(
        description="PostgreSQL server port (for postgres type).",
        default=5432
    )
    database: str = Field(
        description="PostgreSQL database name (for postgres type).",
        default="graphrag"
    )
    username: str | None = Field(
        description="PostgreSQL username for authentication (for postgres type).",
        default=None
    )
    password: str | None = Field(
        description="PostgreSQL password for authentication (for postgres type).",
        default=None
    )
    collection_prefix: str = Field(
        description="Prefix for PostgreSQL collection names (for postgres type).",
        default="graphrag_"
    )
    batch_size: int = Field(
        description="Batch size for database operations (for postgres type).",
        default=50
    )
    command_timeout: int = Field(
        description="Command timeout for database operations (for postgres type).",
        default=600
    )
    server_timeout: int = Field(
        description="Server timeout for database connections (for postgres type).",
        default=120
    )
    connection_timeout: int = Field(
        description="Connection timeout for establishing database connections (for postgres type).",
        default=60
    )