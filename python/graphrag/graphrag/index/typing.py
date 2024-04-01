#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

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
