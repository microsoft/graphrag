# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Indexing Engine overrides package root."""

from .aggregate import aggregate
from .concat import concat
from .merge import merge

__all__ = ["aggregate", "concat", "merge"]
