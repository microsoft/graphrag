# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the split_text method definition."""

import pandas as pd


def split_text(
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
