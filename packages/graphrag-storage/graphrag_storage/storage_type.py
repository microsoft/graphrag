# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License


"""Builtin storage implementation types."""

from enum import StrEnum


class StorageType(StrEnum):
    """Enum for storage types."""

    FILE = "File"
    MEMORY = "Memory"
    AZURE_BLOB = "AzureBlob"
    AZURE_COSMOS = "AzureCosmos"
