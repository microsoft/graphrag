# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field

import graphrag.config.defaults as defs


class VectorStoreConfig(BaseModel):
    """The default configuration section for Vector Store."""

    type: str = Field(
        description="The vector store type to use.", default=defs.VECTOR_STORE_TYPE
    )

    db_uri: str = Field(
        description="The database URI to use.", default=defs.VECTOR_STORE_DB_URI
    )

    collection_name: str = Field(
        description="The database name to use.",
        default=defs.VECTOR_STORE_COLLECTION_NAME,
    )

    overwrite: bool = Field(
        description="Overwrite the existing data.", default=defs.VECTOR_STORE_OVERWRITE
    )
