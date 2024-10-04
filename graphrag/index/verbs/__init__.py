# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing get_default_verbs method definition."""

from .entities import summarize_descriptions
from .graph import (
    create_community_reports,
)

__all__ = [
    "create_community_reports",
    "summarize_descriptions",
]
