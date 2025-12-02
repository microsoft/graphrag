# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License


"""Builtin storage implementation types."""

from enum import StrEnum


class StorageType(StrEnum):
    """Enum for storage types."""

    FILE = "file"
    MEMORY = "memory"
    AZURE_BLOB = "azure_blob"
    AZURE_COSMOS = "azure_cosmos"
