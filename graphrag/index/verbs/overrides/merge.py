# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing merge and _merge_json methods definition."""

# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import logging
from enum import Enum
from typing import Any, cast

import pandas as pd
from datashaper import TableContainer, VerbInput, VerbResult, verb
from datashaper.engine.verbs.merge import merge as ds_merge

log = logging.getLogger(__name__)


class MergeStrategyType(str, Enum):
    """MergeStrategy class definition."""

    json = "json"
    datashaper = "datashaper"

    def __repr__(self):
        """Get a string representation."""
        return f'"{self.value}"'


# TODO: This thing is kinda gross
# Also, it diverges from the original aggregate verb, since it doesn't support the same syntax
@verb(name="merge_override")
def merge(
    input: VerbInput,
    to: str,
    columns: list[str],
    strategy: MergeStrategyType = MergeStrategyType.datashaper,
    delimiter: str = "",
    preserveSource: bool = False,  # noqa N806
    unhot: bool = False,
    prefix: str = "",
    **_kwargs: dict,
) -> TableContainer | VerbResult:
    """Merge method definition."""
    output: pd.DataFrame
    match strategy:
        case MergeStrategyType.json:
            output = _merge_json(input, to, columns)
            filtered_list: list[str] = []

            for col in output.columns:
                try:
                    columns.index(col)
                except ValueError:
                    log.exception("Column %s not found in input columns", col)
                    filtered_list.append(col)

            if not preserveSource:
                output = cast(Any, output[filtered_list])
            return TableContainer(table=output.reset_index())
        case _:
            return ds_merge(
                input, to, columns, strategy, delimiter, preserveSource, unhot, prefix
            )


def _merge_json(
    input: VerbInput,
    to: str,
    columns: list[str],
) -> pd.DataFrame:
    input_table = cast(pd.DataFrame, input.get_input())
    output = input_table
    output[to] = output[columns].apply(
        lambda row: ({**row}),
        axis=1,
    )
    return output
