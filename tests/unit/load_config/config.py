# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Config models for load_config unit tests."""

from pydantic import BaseModel, ConfigDict, Field


class TestNestedModel(BaseModel):
    """Test nested model."""

    model_config = ConfigDict(extra="forbid")

    nested_str: str = Field(description="A nested field.")
    nested_int: int = Field(description="Another nested field.")


class TestConfigModel(BaseModel):
    """Test configuration model."""

    model_config = ConfigDict(extra="forbid")
    __test__ = False  # type: ignore

    name: str = Field(description="Name field.")
    value: int = Field(description="Value field.")
    nested: TestNestedModel = Field(description="Nested model field.")
    nested_list: list[TestNestedModel] = Field(description="List of nested models.")
