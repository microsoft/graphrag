# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'Replacement' model."""

from dataclasses import dataclass


@dataclass
class Replacement:
    """Replacement class definition."""

    pattern: str
    replacement: str
