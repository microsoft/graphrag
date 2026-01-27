# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Parameterization settings for the default configuration."""

import re

from pydantic import BaseModel, Field, model_validator

DEFAULT_VECTOR_SIZE: int = 3072

VALID_IDENTIFIER_REGEX = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def is_valid_field_name(field: str) -> bool:
    """Check if a field name is valid for CosmosDB."""
    return bool(VALID_IDENTIFIER_REGEX.match(field))


class IndexSchema(BaseModel):
    """The default configuration section for Vector Store Schema."""

    index_name: str = Field(
        description="The index name to use.", default="vector_index"
    )

    id_field: str = Field(
        description="The ID field to use.",
        default="id",
    )

    vector_field: str = Field(
        description="The vector field to use.",
        default="vector",
    )

    vector_size: int = Field(
        description="The vector size to use.",
        default=DEFAULT_VECTOR_SIZE,
    )

    def _validate_schema(self) -> None:
        """Validate the schema."""
        for field in [
            self.id_field,
            self.vector_field,
        ]:
            if not is_valid_field_name(field):
                msg = f"Unsafe or invalid field name: {field}"
                raise ValueError(msg)

    @model_validator(mode="after")
    def _validate_model(self):
        """Validate the model."""
        self._validate_schema()
        return self
