# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Typing module."""

from dataclasses import dataclass
from enum import Enum

import pandas as pd


class SearchType(Enum):
    """SearchType class definition."""

    Basic = "basic"
    Local = "local"
    Global = "global"
    Drift = "drift"


@dataclass
class SearchResult:
    """SearchResult class definition."""

    # create a dataclass to store the search result of each algorithm
    search_type: SearchType
    response: str
    context: dict[str, pd.DataFrame]
