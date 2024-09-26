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

    nodes = unpack_graph_df(table, callbacks, "clustered_graph", "nodes")
    nodes.rename(columns={"label": "name"}, inplace=True)

    nodes = cast(
        pd.DataFrame,
        nodes[
            [
                "id",
                "name",
                "type",
                "description",
                "human_readable_id",
                "graph_embedding",
                "source_id",
            ]
        ],
    )

    # create_base_entity_graph has multiple levels of clustering, which means there are multiple graphs with the same entities
    # this dedupes the entities so that there is only one of each entity
    nodes.drop_duplicates(subset="id", inplace=True)

    # eliminate empty names
    filtered = cast(pd.DataFrame, nodes[nodes["name"].notna()].reset_index(drop=True))

    with_ids = text_split_df(
        filtered, column="source_id", separator=",", to="text_unit_ids"
    )
    with_ids.drop(columns=["source_id"], inplace=True)

    embedded = with_ids

    if not skip_name_embedding:
        embedded = await text_embed_df(
            embedded,
            callbacks,
            cache,
            column="name",
            strategy=name_text_embed["strategy"],
            to="name_embedding",
            embedding_name="entity_name",
        )

    if not skip_description_embedding:
        # description embedding is a concat of the name + description, so we'll create a temporary column
        embedded["name_description"] = embedded["name"] + ":" + embedded["description"]
        embedded = await text_embed_df(
            embedded,
            callbacks,
            cache,
            column="name_description",
            strategy=description_text_embed["strategy"],
            to="description_embedding",
            embedding_name="entity_name_description",
        )
        embedded.drop(columns=["name_description"], inplace=True)
        is_using_vector_store = (
            description_text_embed.get("strategy", {}).get("vector_store", None)
            is not None
        )
        if not is_using_vector_store:
            embedded = embedded[embedded["description_embedding"].notna()].reset_index(
                drop=True
            )

    return create_verb_result(cast(Table, embedded))
