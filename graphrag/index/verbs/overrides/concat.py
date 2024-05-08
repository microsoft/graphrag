# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing concat method definition."""

# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
from typing import cast

import pandas as pd
from datashaper import TableContainer, VerbInput, verb


@verb(name="concat_override")
def concat(
    input: VerbInput,
    columnwise: bool = False,
    **_kwargs: dict,
) -> TableContainer:
    """Concat method definition."""
    input_table = cast(pd.DataFrame, input.get_input())
    others = cast(list[pd.DataFrame], input.get_others())
    if columnwise:
        output = pd.concat([input_table, *others], axis=1)
    else:
        output = pd.concat([input_table, *others], ignore_index=True)
    return TableContainer(table=output)
