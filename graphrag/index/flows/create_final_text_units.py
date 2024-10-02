# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform the text units."""

from typing import cast

import pandas as pd
from datashaper import (
    VerbCallbacks,
)

from graphrag.index.cache import PipelineCache
from graphrag.index.operations.embed_text.embed_text import embed_text


async def create_final_text_units(
    text_units: pd.DataFrame,
    final_entities: pd.DataFrame,
    final_relationships: pd.DataFrame,
    final_covariates: pd.DataFrame | None,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    text_text_embed: dict | None = None,
) -> pd.DataFrame:
    """All the steps to transform the text units."""
    selected = text_units.loc[:, ["id", "chunk", "document_ids", "n_tokens"]].rename(
        columns={"chunk": "text"}
    )

    entity_join = _entities(final_entities)
    relationship_join = _relationships(final_relationships)

    entity_joined = _join(selected, entity_join)
    relationship_joined = _join(entity_joined, relationship_join)
    final_joined = relationship_joined

    if final_covariates is not None:
        covariate_join = _covariates(final_covariates)
        final_joined = _join(relationship_joined, covariate_join)

    aggregated = final_joined.groupby("id", sort=False).agg("first").reset_index()

    is_using_vector_store = False
    if text_text_embed:
        aggregated["text_embedding"] = await embed_text(
            aggregated,
            callbacks,
            cache,
            column="text",
            strategy=text_text_embed["strategy"],
        )
        is_using_vector_store = (
            text_text_embed.get("strategy", {}).get("vector_store", None) is not None
        )

    return cast(
        pd.DataFrame,
        aggregated[
            [
                "id",
                "text",
                *(
                    []
                    if (not text_text_embed or is_using_vector_store)
                    else ["text_embedding"]
                ),
                "n_tokens",
                "document_ids",
                "entity_ids",
                "relationship_ids",
                *([] if final_covariates is None else ["covariate_ids"]),
            ]
        ],
    )


def _entities(df: pd.DataFrame) -> pd.DataFrame:
    selected = df.loc[:, ["id", "text_unit_ids"]]
    unrolled = selected.explode(["text_unit_ids"]).reset_index(drop=True)

    return (
        unrolled.groupby("text_unit_ids", sort=False)
        .agg(entity_ids=("id", "unique"))
        .reset_index()
        .rename(columns={"text_unit_ids": "id"})
    )


def _relationships(df: pd.DataFrame) -> pd.DataFrame:
    selected = df.loc[:, ["id", "text_unit_ids"]]
    unrolled = selected.explode(["text_unit_ids"]).reset_index(drop=True)

    return (
        unrolled.groupby("text_unit_ids", sort=False)
        .agg(relationship_ids=("id", "unique"))
        .reset_index()
        .rename(columns={"text_unit_ids": "id"})
    )


def _covariates(df: pd.DataFrame) -> pd.DataFrame:
    selected = df.loc[:, ["id", "text_unit_id"]]

    return (
        selected.groupby("text_unit_id", sort=False)
        .agg(covariate_ids=("id", "unique"))
        .reset_index()
        .rename(columns={"text_unit_id": "id"})
    )


def _join(left, right):
    return left.merge(
        right,
        on="id",
        how="left",
        suffixes=["_1", "_2"],
    )
