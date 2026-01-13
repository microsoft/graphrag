# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Common types for vector stores."""

from collections.abc import Callable

TextEmbedder = Callable[[str], list[float]]
