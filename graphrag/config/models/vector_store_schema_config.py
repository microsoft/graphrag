# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

from pydantic import BaseModel, Field, model_validator

DEFAULT_VECTOR_SIZE: int = 1536

class VectorStoreSchemaConfig(BaseModel):
    """The default configuration section for Vector Store Schema."""

    index_name: str = Field(
        description="The index name to use.",
        default=""
    )

    id_field: str = Field(
        description="The ID field to use.",
        default="id",
    )

    vector_field: str = Field(
        description="The vector field to use.",
        default="vector",
    )

    text_field: str = Field(
        description="The text field to use.",
        default="text",
    )

    attributes_field: str = Field(
        description="The attributes field to use.",
        default="attributes",
    )

    vector_size: int = Field(
        description="The vector size to use.",
        default=DEFAULT_VECTOR_SIZE,
    )

    #TODO GAUDY
    def _validate_schema(self) -> None:
        """Validate the schema."""

    @model_validator(mode="after")
    def _validate_model(self):
        """Validate the model."""
        self._validate_schema()
        return self
