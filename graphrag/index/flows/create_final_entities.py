# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final entities."""

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.index.cache import PipelineCache
from graphrag.index.operations.embed_text import embed_text
from graphrag.index.operations.unpack_graph import unpack_graph


async def create_final_entities(
    entity_graph: pd.DataFrame,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    name_text_embed: dict | None = None,
    description_text_embed: dict | None = None,
) -> pd.DataFrame:
    """All the steps to transform final entities."""
    # Process nodes
    nodes = (
        unpack_graph(entity_graph, callbacks, "clustered_graph", "nodes")
        .rename(columns={"label": "name"})
        .loc[
            :,
            [
                "id",
                "name",
                "type",
                "description",
                "human_readable_id",
                "source_id",
            ],
        ]
        .drop_duplicates(subset="id")
    )

    nodes = nodes.loc[nodes["name"].notna()]

    nodes["text_unit_ids"] = nodes["source_id"].str.split(",")
    nodes.drop(columns=["source_id"], inplace=True)

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
