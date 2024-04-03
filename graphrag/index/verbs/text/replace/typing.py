# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""A module containing 'Replacement' model."""

from dataclasses import dataclass


@dataclass
class Replacement:
    """Replacement class definition."""

    pattern: str
    replacement: str
