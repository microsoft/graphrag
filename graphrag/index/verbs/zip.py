# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing ds_zip method definition."""

from typing import cast

import pandas as pd
from datashaper import TableContainer, VerbInput, verb


@verb(name="zip")
def zip_verb(
    input: VerbInput,
    to: str,
    columns: list[str],
    type: str | None = None,  # noqa A002
    **_kwargs: dict,
) -> TableContainer:
    """
    Zip columns together.

    ## Usage
    TODO

    """
    table = cast(pd.DataFrame, input.get_input())
    if type is None:
        table[to] = list(zip(*[table[col] for col in columns], strict=True))

    # This one is a little weird
    elif type == "dict":
        if len(columns) != 2:
            msg = f"Expected exactly two columns for a dict, got {columns}"
            raise ValueError(msg)
        key_col, value_col = columns

        results = []
        for _, row in table.iterrows():
            keys = row[key_col]
            values = row[value_col]
            output = {}
            if len(keys) != len(values):
                msg = f"Expected same number of keys and values, got {len(keys)} keys and {len(values)} values"
                raise ValueError(msg)
            for idx, key in enumerate(keys):
                output[key] = values[idx]
            results.append(output)

        table[to] = results
    return TableContainer(table=table.reset_index(drop=True))
