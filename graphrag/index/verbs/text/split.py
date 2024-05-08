# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the text_split method definition."""

from typing import cast

import pandas as pd
from datashaper import TableContainer, VerbInput, verb


@verb(name="text_split")
def text_split(
    input: VerbInput,
    column: str,
    to: str,
    separator: str = ",",
    **_kwargs: dict,
) -> TableContainer:
    """
    Split a piece of text into a list of strings based on a delimiter. The verb outputs a new column containing a list of strings.

    ## Usage

    ```yaml
    verb: text_split
    args:
        column: text # The name of the column containing the text to split
        to: split_text # The name of the column to output the split text to
        separator: "," # The separator to split the text on, defaults to ","
    ```
    """
    output = text_split_df(cast(pd.DataFrame, input.get_input()), column, to, separator)
    return TableContainer(table=output)


def text_split_df(
    input: pd.DataFrame, column: str, to: str, separator: str = ","
) -> pd.DataFrame:
    """Split a column into a list of strings."""
    output = input

    def _apply_split(row):
        if row[column] is None or isinstance(row[column], list):
            return row[column]
        if row[column] == "":
            return []
        if not isinstance(row[column], str):
            message = f"Expected {column} to be a string, but got {type(row[column])}"
            raise TypeError(message)
        return row[column].split(separator)

    output[to] = output.apply(_apply_split, axis=1)
    return output
