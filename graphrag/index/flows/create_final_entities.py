# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final entities."""

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.index.cache import PipelineCache
from graphrag.index.operations.embed_text.embed_text import embed_text
from graphrag.index.verbs.graph.unpack import unpack_graph_df
from graphrag.index.verbs.text.split import text_split_df


async def create_final_entities(
    entity_graph: pd.DataFrame,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    name_text_embed: dict,
    description_text_embed: dict,
) -> pd.DataFrame:
    """All the steps to transform final entities."""
    # Process nodes
    nodes = (
        unpack_graph_df(entity_graph, callbacks, "clustered_graph", "nodes")
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
    if name_text_embed:
        nodes["name_embedding"] = await embed_text(
            nodes,
            callbacks,
            cache,
            column="name",
            strategy=name_text_embed["strategy"],
            embedding_name="entity_name",
        )

    # Embed description if not skipped
    if description_text_embed:
        # Concatenate 'name' and 'description' and embed
        nodes["name_description"] = nodes["name"] + ":" + nodes["description"]
        nodes["description_embedding"] = await embed_text(
            nodes,
            callbacks,
            cache,
            column="name_description",
            strategy=description_text_embed["strategy"],
            embedding_name="entity_name_description",
        )

        # Drop rows with NaN 'description_embedding' if not using vector store
        if not description_text_embed.get("strategy", {}).get("vector_store"):
            nodes = nodes.loc[nodes["description_embedding"].notna()]
        nodes.drop(columns="name_description", inplace=True)

    return nodes
