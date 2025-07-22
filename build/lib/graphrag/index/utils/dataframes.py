# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing DataFrame utilities."""

from collections.abc import Callable
from typing import Any, cast

import pandas as pd
from pandas._typing import MergeHow


def drop_columns(df: pd.DataFrame, *column: str) -> pd.DataFrame:
    """Drop columns from a dataframe."""
    return df.drop(list(column), axis=1)


def where_column_equals(df: pd.DataFrame, column: str, value: Any) -> pd.DataFrame:
    """Return a filtered DataFrame where a column equals a value."""
    return cast("pd.DataFrame", df[df[column] == value])


def antijoin(df: pd.DataFrame, exclude: pd.DataFrame, column: str) -> pd.DataFrame:
    """Return an anti-joined dataframe.

    Arguments:
    * df: The DataFrame to apply the exclusion to
    * exclude: The DataFrame containing rows to remove.
    * column: The join-on column.
    """
    return df.loc[~df.loc[:, column].isin(exclude.loc[:, column])]


def transform_series(series: pd.Series, fn: Callable[[Any], Any]) -> pd.Series:
    """Apply a transformation function to a series."""
    return cast("pd.Series", series.apply(fn))


def join(
    left: pd.DataFrame, right: pd.DataFrame, key: str, strategy: MergeHow = "left"
) -> pd.DataFrame:
    """Perform a table join."""
    return left.merge(right, on=key, how=strategy)


def union(*frames: pd.DataFrame) -> pd.DataFrame:
    """Perform a union operation on the given set of dataframes."""
    return pd.concat(list(frames))


def select(df: pd.DataFrame, *columns: str) -> pd.DataFrame:
    """Select columns from a dataframe."""
    return cast("pd.DataFrame", df[list(columns)])
