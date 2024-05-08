# Copyright (c) 2024 Microsoft Corporation.

"""A package containing the 'Named' protocol."""

from dataclasses import dataclass

from .identified import Identified


@dataclass
class Named(Identified):
    """A protocol for an item with a name/title."""

    title: str
    """The name/title of the item."""
