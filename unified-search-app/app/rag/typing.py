"""
Copyright (c) Microsoft Corporation. All rights reserved.
"""

from dataclasses import dataclass
from enum import Enum

import pandas as pd


class SearchType(Enum):
    Basic = "basic"
    Local = "local"
    Global = "global"
    Drift = "drift"


@dataclass
class SearchResult:
    # create a dataclass to store the search result of each algorithm
    search_type: SearchType
    response: str
    context: dict[str, pd.DataFrame]
