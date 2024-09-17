# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final communities."""

from functools import partial
from typing import Any, cast

import pandas as pd
from datashaper import (
    Criterion,
    FilterArgs,
    FilterCompareType,
    StringComparisonOperator,
    Table,
    VerbCallbacks,
    VerbInput,
    filter_df,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result
from pandas._typing import Suffixes
from pandas.api.types import is_bool

from graphrag.index.verbs.graph.unpack import unpack_graph_df
from graphrag.index.verbs.overrides.aggregate import aggregate_df


@verb(name="create_final_communities", treats_input_tables_as_immutable=True)
def create_final_communities(
    input: VerbInput,
    callbacks: VerbCallbacks,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform final communities."""
    table = cast(pd.DataFrame, input.get_input())

    graph_nodes = unpack_graph_df(table, callbacks, "clustered_graph", "nodes")
    graph_edges = unpack_graph_df(table, callbacks, "clustered_graph", "edges")

    source_clusters = graph_nodes.merge(
        graph_edges,
        left_on="label",
        right_on="source",
        how="inner",
        suffixes=cast(Suffixes, ["_1", "_2"]),
    )
    target_clusters = graph_nodes.merge(
        graph_edges,
        left_on="label",
        right_on="target",
        how="inner",
        suffixes=cast(Suffixes, ["_1", "_2"]),
    )

    concatenated_clusters = pd.concat(
        [source_clusters, target_clusters], ignore_index=True
    )

    combined_clusters = _filter_clusters(concatenated_clusters)

    cluster_relationships = aggregate_df(
        combined_clusters,
        aggregations=[
            {
                "column": "id_2",  # this is the id of the edge from the join steps above
                "to": "relationship_ids",
                "operation": "array_agg_distinct",
            },
            {
                "column": "source_id_1",
                "to": "text_unit_ids",
                "operation": "array_agg_distinct",
            },
        ],
        groupby=[
            "cluster",
            "level_1",  # level_1 is the left side of the join
        ],
    )

    all_clusters = aggregate_df(
        graph_nodes,
        aggregations=[{"column": "cluster", "to": "id", "operation": "any"}],
        groupby=["cluster", "level"],
    )

    joined = all_clusters.merge(
        cluster_relationships,
        left_on="id",
        right_on="cluster",
        how="inner",
        suffixes=cast(Suffixes, ["_1", "_2"]),
    )

    filtered = _filter_secondary(joined)

    titled = _create_title(filtered)

    titled["raw_community"] = titled[
        "id"
    ]  # TODO: Rodrigo says "raw_community" is temporary
    return create_verb_result(
        cast(
            Table,
            titled[
                [
                    "id",
                    "title",
                    "level",
                    "raw_community",
                    "relationship_ids",
                    "text_unit_ids",
                ]
            ],
        )
    )


def _filter_clusters(table: pd.DataFrame) -> pd.DataFrame:
    # level_1 is the left side of the join
    # level_2 is the right side of the join
    args = FilterArgs(
        column="level_1",
        criteria=[
            Criterion(
                type=FilterCompareType.Column,
                operator=StringComparisonOperator.Equals,
                value="level_2",
            ),
        ],
    )
    filter_index = filter_df(table, args)
    sub_idx = filter_index == True  # noqa: E712
    idx = filter_index[sub_idx].index  # type: ignore
    return cast(pd.DataFrame, table[table.index.isin(idx)].reset_index(drop=True))


# we've filtered on the left, now we filter on the right
def _filter_secondary(table: pd.DataFrame) -> pd.DataFrame:
    args = FilterArgs(
        column="level",
        criteria=[
            Criterion(
                type=FilterCompareType.Column,
                operator=StringComparisonOperator.Equals,
                value="level_1",
            ),
        ],
    )
    filter_index = filter_df(table, args)
    sub_idx = filter_index == True  # noqa: E712
    idx = filter_index[sub_idx].index  # type: ignore
    return cast(pd.DataFrame, table[table.index.isin(idx)].reset_index(drop=True))


def _create_title(table: pd.DataFrame) -> pd.DataFrame:
    table["__temp"] = "Community"

    table["title"] = table[["__temp", "id"]].apply(
        partial(
            lambda values, delim, **_kwargs: _create_array(values, delim), delim=""
        ),
        axis=1,
    )

    return table


def _correct_type(value: Any) -> str | int | Any:
    if is_bool(value):
        return str(value).lower()
    try:
        return int(value) if value.is_integer() else value
    except AttributeError:
        return value


def _create_array(column: pd.Series, delim: str) -> str:
    col: pd.DataFrame | pd.Series = column.dropna().apply(lambda x: _correct_type(x))
    return delim.join(col.astype(str))
