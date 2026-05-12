# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Storage configuration model."""

from pydantic import BaseModel, ConfigDict, Field

from graphrag_storage.tables.table_type import TableType


class TableProviderConfig(BaseModel):
    """The default configuration section for table providers."""

    model_config = ConfigDict(extra="allow")
    """Allow extra fields to support custom table provider implementations."""

    type: str = Field(
        description="The table type to use. Builtin types include 'parquet', 'csv', and 'cosmosdb'.",
        default=TableType.Parquet,
    )

    container_name: str | None = Field(
        description="The Cosmos DB container name for table storage.",
        default=None,
    )

    legacy_container: str | None = Field(
        description="Optional legacy Cosmos DB container name for read-time migration fallback.",
        default=None,
    )

    batch_size: int = Field(
        description="Number of documents per transactional batch write for Cosmos DB. Max 100.",
        default=50,
    )
