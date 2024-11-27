# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Exporter protocol for exporting dataframe's to a destination."""

from typing import Protocol

import pandas as pd


class Exporter(Protocol):
    """TableExporter protocol for exporting tables to a destination."""

    async def export(self, name: str, data: pd.DataFrame) -> None:
        """Export a dataframe to storage."""
