# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing genid method definition."""

from typing import cast

import pandas as pd
from datashaper import TableContainer, VerbInput, verb

from graphrag.index.utils import gen_md5_hash


@verb(name="genid")
def genid(
    input: VerbInput,
    to: str,
    method: str = "md5_hash",
    hash: list[str] = [],  # noqa A002
    **_kwargs: dict,
) -> TableContainer:
    """
    Generate a unique id for each row in the tabular data.

    ## Usage
    ### json
    ```json
    {
        "verb": "genid",
        "args": {
            "to": "id_output_column_name", /* The name of the column to output the id to */
            "method": "md5_hash", /* The method to use to generate the id */
            "hash": ["list", "of", "column", "names"] /* only if using md5_hash */,
            "seed": 034324 /* The random seed to use with UUID */
        }
    }
    ```

    ### yaml
    ```yaml
    verb: genid
    args:
        to: id_output_column_name
        method: md5_hash
        hash:
            - list
            - of
            - column
            - names
        seed: 034324
    ```
    """
    data = cast(pd.DataFrame, input.source.table)

    if method == "md5_hash":
        if len(hash) == 0:
            msg = 'Must specify the "hash" columns to use md5_hash method'
            raise ValueError(msg)

        data[to] = data.apply(lambda row: gen_md5_hash(row, hash), axis=1)
    elif method == "increment":
        data[to] = data.index + 1
    else:
        msg = f"Unknown method {method}"
        raise ValueError(msg)
    return TableContainer(table=data)
