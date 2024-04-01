#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""A module containing concat method definition."""
#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#
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
