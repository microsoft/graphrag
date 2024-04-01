#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""A module containing unzip method definition."""
from typing import cast

import pandas as pd
from datashaper import TableContainer, VerbInput, verb


# TODO: Check if this is already a thing
# Takes 1|(x,y)|b
# and converts to
# 1|x|y|b
@verb(name="unzip")
def unzip(
    input: VerbInput, column: str, to: list[str], **_kwargs: dict
) -> TableContainer:
    """Unpacks a column containing a tuple into multiple columns."""
    table = cast(pd.DataFrame, input.get_input())

    table[to] = pd.DataFrame(table[column].tolist(), index=table.index)

    return TableContainer(table=table)
