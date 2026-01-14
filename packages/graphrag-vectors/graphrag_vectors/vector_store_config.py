# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
        description="The database URL when type == azure_ai_search.",
        default=None,
    )

    def _validate_url(self) -> None:
        """Validate the database URL."""
        if (
            self.type == VectorStoreType.AzureAISearch
            or self.type == VectorStoreType.CosmosDB
        ) and (self.url is None or self.url.strip() == ""):
            msg = "vector_store.url is required when vector_store.type == azure_ai_search or cosmos_db."
            raise ValueError(msg)

    api_key: str | None = Field(
        description="The database API key when type == azure_ai_search.",
        default=None,
    )

    audience: str | None = Field(
        description="The database audience when type == azure_ai_search.",
        default=None,
    )

    index_prefix: str | None = Field(
        description="Prefix to apply to all index names. Suitable for partitioning projects. If you want full customization of each index name, leave this None and create an index_schema entry.",
        default=None,
    )

    database_name: str | None = Field(
        description="The database name to use when type == cosmos_db.",
        default=None,
    )

    index_schema: dict[str, IndexSchema] = {}

    def _validate_schema(self) -> None:
        """Validate the index schema."""
        if self.type == VectorStoreType.CosmosDB:
            for id_field in self.index_schema:
                if id_field != "id":
                    msg = "When using CosmosDB, the id_field in index_schema must be 'id'. Please update your settings.yaml and set the id_field to 'id'."
                    raise ValueError(msg)

    @model_validator(mode="after")
    def _validate_model(self):
        """Validate the model."""
        self._validate_url()
        self._validate_schema()
        return self
