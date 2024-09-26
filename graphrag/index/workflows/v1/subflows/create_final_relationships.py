# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final relationships."""

from typing import Any, cast

import pandas as pd
from datashaper import (
    Table,
    VerbCallbacks,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.cache import PipelineCache
from graphrag.index.utils.ds_util import get_required_input_table
from graphrag.index.verbs.graph.compute_edge_combined_degree import (
    compute_edge_combined_degree_df,
)
from graphrag.index.verbs.graph.unpack import unpack_graph_df
from graphrag.index.verbs.text.embed.text_embed import text_embed_df


@verb(
    name="create_final_relationships",
    treats_input_tables_as_immutable=True,
)
async def create_final_relationships(
    input: VerbInput,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    text_embed: dict,
    skip_embedding: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform final relationships."""
    table = cast(pd.DataFrame, input.get_input())
    nodes = cast(pd.DataFrame, get_required_input_table(input, "nodes").table)

    graph_edges = unpack_graph_df(table, callbacks, "clustered_graph", "edges")

    graph_edges.rename(columns={"source_id": "text_unit_ids"}, inplace=True)

    filtered = cast(
        pd.DataFrame, graph_edges[graph_edges["level"] == 0].reset_index(drop=True)
    )

    if not skip_embedding:
        filtered = await text_embed_df(
            filtered,
            callbacks,
            cache,
            column="description",
            strategy=text_embed["strategy"],
            to="description_embedding",
            embedding_name="relationship_description",
        )

    pruned_edges = filtered.drop(columns=["level"])

    filtered_nodes = cast(
        pd.DataFrame,
        nodes[nodes["level"] == 0].reset_index(drop=True)[["title", "degree"]],
    )

    edge_combined_degree = compute_edge_combined_degree_df(
        pruned_edges,
        filtered_nodes,
        to="rank",
        node_name_column="title",
        node_degree_column="degree",
        edge_source_column="source",
        edge_target_column="target",
    )

    edge_combined_degree["human_readable_id"] = edge_combined_degree[
        "human_readable_id"
    ].astype(str)
    edge_combined_degree["text_unit_ids"] = _to_array(
        edge_combined_degree["text_unit_ids"], ","
    )

    return create_verb_result(cast(Table, edge_combined_degree))


# from datashaper, we should be able to inline this
def _to_array(column, delimiter: str):
    def convert_value(value: Any) -> list:
        if pd.isna(value):
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return value.split(delimiter)
        return [value]

    return column.apply(convert_value)
