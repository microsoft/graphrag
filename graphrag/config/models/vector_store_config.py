# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field, model_validator

import graphrag.config.defaults as defs
from graphrag.vector_stores.factory import VectorStoreType


class VectorStoreConfig(BaseModel):
    """The default configuration section for Vector Store."""

    type: str = Field(
        description="The vector store type to use.",
        default=defs.VECTOR_STORE_TYPE,
    )

    db_uri: str | None = Field(description="The database URI to use.", default=None)

    def _validate_db_uri(self) -> None:
        """Validate the database URI."""
        if self.type == VectorStoreType.LanceDB.value and (
            self.db_uri is None or self.db_uri.strip() == ""
        ):
            self.db_uri = defs.VECTOR_STORE_DB_URI

        if self.type != VectorStoreType.LanceDB.value and (
            self.db_uri is not None and self.db_uri.strip() != ""
        ):
            msg = "vector_store.db_uri is only used when vector_store.type == lancedb. Please rerun `graphrag init` and select the correct vector store type."
            raise ValueError(msg)

    url: str | None = Field(
        description="The database URL when type == azure_ai_search.",
        default=None,
    )

    def _validate_url(self) -> None:
        """Validate the database URL."""
        if self.type == VectorStoreType.AzureAISearch and (
            self.url is None or self.url.strip() == ""
        ):
            msg = "vector_store.url is required when vector_store.type == azure_ai_search. Please rerun `graphrag init` and select the correct vector store type."
            raise ValueError(msg)

        if self.type != VectorStoreType.AzureAISearch and (
            self.url is not None and self.url.strip() != ""
        ):
            msg = "vector_store.url is only used when vector_store.type == azure_ai_search. Please rerun `graphrag init` and select the correct vector store type."
            raise ValueError(msg)

    api_key: str | None = Field(
        description="The database API key when type == azure_ai_search.",
        default=None,
    )

    audience: str | None = Field(
        description="The database audience when type == azure_ai_search.",
        default=None,
    )

    container_name: str = Field(
        description="The database name to use.",
        default=defs.VECTOR_STORE_CONTAINER_NAME,
    )

    overwrite: bool = Field(
        description="Overwrite the existing data.", default=defs.VECTOR_STORE_OVERWRITE
    )

    @model_validator(mode="after")
    def _validate_model(self):
        """Validate the model."""
        self._validate_db_uri()
        self._validate_url()
        return self
