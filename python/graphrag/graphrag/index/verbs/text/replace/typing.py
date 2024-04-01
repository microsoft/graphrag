#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""A module containing 'Replacement' model."""
from dataclasses import dataclass


@dataclass
class Replacement:
    """Replacement class definition."""

    pattern: str
    replacement: str
