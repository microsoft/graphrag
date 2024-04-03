# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""The Indexing Engine entities package root."""

from .extraction import entity_extract
from .summarize import summarize_descriptions

__all__ = ["entity_extract", "summarize_descriptions"]
