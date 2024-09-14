# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The Indexing Engine workflows -> subflows package root."""

from .join_text_units_to_entity_ids import join_text_units_to_entity_ids

__all__ = [
    "join_text_units_to_entity_ids",
]
