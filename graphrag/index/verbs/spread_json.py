# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing spread_json method definition."""

import logging

import pandas as pd
from datashaper import TableContainer, VerbInput, verb

from graphrag.index.utils import is_null

# TODO: Check if this is already a thing
DEFAULT_COPY = ["level"]


@verb(name="spread_json")
def spread_json(
    input: VerbInput,
    column: str,
    copy: list[str] | None = None,
    **_kwargs: dict,
) -> TableContainer:
    """
    Unpack a column containing a tuple into multiple columns.

    id|json|b
    1|{"x":5,"y":6}|b

    is converted to

    id|x|y|b
    --------
    1|5|6|b
    """
    if copy is None:
        copy = DEFAULT_COPY
    data = input.get_input()

    results = []
    for _, row in data.iterrows():
        try:
            cleaned_row = {col: row[col] for col in copy}
            rest_row = row[column] if row[column] is not None else {}

            if is_null(rest_row):
                rest_row = {}

            results.append({**cleaned_row, **rest_row})  # type: ignore
        except Exception:
            logging.exception("Error spreading row: %s", row)
            raise
    data = pd.DataFrame(results, index=data.index)

    return TableContainer(table=data)
