# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

# Use this for now instead of a wrapper
"""A module containing 'NodePosition' model."""

from dataclasses import dataclass


@dataclass
class NodePosition:
    """Node position class definition."""

    label: str
    cluster: str
    size: float

    x: float
    y: float
    z: float | None = None

    def to_pandas(self) -> tuple[str, float, float, str, float]:
        """To pandas method definition."""
        return self.label, self.x, self.y, self.cluster, self.size


GraphLayout = list[NodePosition]
