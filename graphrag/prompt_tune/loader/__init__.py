# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Fine-tuning config and data loader module."""

from .input import MIN_CHUNK_OVERLAP, MIN_CHUNK_SIZE, load_docs_in_chunks

__all__ = [
    "MIN_CHUNK_OVERLAP",
    "MIN_CHUNK_SIZE",
    "load_docs_in_chunks",
]
