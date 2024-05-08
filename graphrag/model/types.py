# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Common types for the GraphRAG knowledge model."""

from collections.abc import Callable

TextEmbedder = Callable[[str], list[float]]
