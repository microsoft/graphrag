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
        description="The table type to use.",
        default=TableType.Parquet,
    )
