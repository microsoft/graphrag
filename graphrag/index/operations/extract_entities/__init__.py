# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Indexing Engine entities extraction package root."""

from graphrag.index.operations.extract_entities.extract_entities import (
    ExtractEntityStrategyType,
    extract_entities,
)

__all__ = ["ExtractEntityStrategyType", "extract_entities"]
