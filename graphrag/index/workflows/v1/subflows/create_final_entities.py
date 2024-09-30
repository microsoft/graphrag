# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final entities."""

from typing import cast

import pandas as pd
from datashaper import (
    Table,
    VerbCallbacks,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.cache import PipelineCache
from graphrag.index.verbs.graph.unpack import unpack_graph_df
from graphrag.index.verbs.text.embed.text_embed import text_embed_df
from graphrag.index.verbs.text.split import text_split_df


@verb(
    name="create_final_entities",
    treats_input_tables_as_immutable=True,
)
async def create_final_entities(
    input: VerbInput,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    name_text_embed: dict,
    description_text_embed: dict,
    skip_name_embedding: bool = False,
    skip_description_embedding: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform final entities."""
    table = cast(pd.DataFrame, input.get_input())

    # Process nodes
    nodes = (
        unpack_graph_df(table, callbacks, "clustered_graph", "nodes")
        .rename(columns={"label": "name"})
        .loc[
            :,
            [
                "id",
                "name",
                "type",
                "description",
                "human_readable_id",
                "graph_embedding",
                "source_id",
            ],
        ]
        .drop_duplicates(subset="id")
    )

    nodes = nodes.loc[nodes["name"].notna()]

    # Split 'source_id' column into 'text_unit_ids'
    nodes = text_split_df(
        nodes, column="source_id", separator=",", to="text_unit_ids"
    ).drop(columns=["source_id"])

    # Embed name if not skipped
    if not skip_name_embedding:
        nodes = await text_embed_df(
            nodes,
            callbacks,
            cache,
            column="name",
            strategy=name_text_embed["strategy"],
            to="name_embedding",
            embedding_name="entity_name",
        )

    # Embed description if not skipped
    if not skip_description_embedding:
        # Concatenate 'name' and 'description' and embed
        nodes = await text_embed_df(
            nodes.assign(name_description=nodes["name"] + ":" + nodes["description"]),
            callbacks,
            cache,
            column="name_description",
            strategy=description_text_embed["strategy"],
            to="description_embedding",
            embedding_name="entity_name_description",
        )

        # Drop rows with NaN 'description_embedding' if not using vector store
        if not description_text_embed.get("strategy", {}).get("vector_store"):
            nodes = nodes.loc[nodes["description_embedding"].notna()]
        nodes.drop(columns="name_description", inplace=True)

    # Return final result
    return create_verb_result(cast(Table, nodes))
