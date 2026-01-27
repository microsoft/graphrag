# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, ConfigDict, Field

from graphrag_vectors.index_schema import IndexSchema
from graphrag_vectors.vector_store_type import VectorStoreType


class VectorStoreConfig(BaseModel):
    """The default configuration section for Vector Store."""

    model_config = ConfigDict(extra="allow")
    """Allow extra fields to support custom vector implementations."""

    type: str = Field(
        description="The vector store type to use.",
        default=VectorStoreType.LanceDB,
    )

    db_uri: str | None = Field(
        description="The database URI to use (only used by lancedb for built-in stores).",
        default=None,
    )

    url: str | None = Field(
        description="The database URL when type == azure_ai_search or cosmosdb.",
        default=None,
    )

    api_key: str | None = Field(
        description="The database API key when type == azure_ai_search.",
        default=None,
    )

    audience: str | None = Field(
        description="The database audience when type == azure_ai_search.",
        default=None,
    )

    connection_string: str | None = Field(
        description="The connection string when type == cosmosdb.",
        default=None,
    )

    database_name: str | None = Field(
        description="The database name to use when type == cosmosdb.",
        default=None,
    )

    index_schema: dict[str, IndexSchema] = {}
