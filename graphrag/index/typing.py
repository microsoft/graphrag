# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the 'PipelineRunResult' model."""

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

ErrorHandlerFn = Callable[[BaseException | None, str | None, dict | None], None]


@dataclass
class PipelineRunResult:
    """Pipeline run result class definition."""

    workflow: str
    result: pd.DataFrame | None
    errors: list[BaseException] | None
