# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform before we embed the text units."""

from typing import cast

import pandas as pd
from datashaper.engine.verbs.verb_input import VerbInput
from datashaper.engine.verbs.verbs_mapping import verb
from datashaper.table_store.types import Table, VerbResult, create_verb_result


@verb(
    name="create_final_text_units_pre_embedding", treats_input_tables_as_immutable=True
)
def create_final_text_units_pre_embedding(
    input: VerbInput,
    covariates_enabled: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform before we embed the text units."""
    table = cast(pd.DataFrame, input.get_input())
    others = input.get_others()

    selected = table.loc[:, ["id", "chunk", "document_ids", "n_tokens"]].rename(
        columns={"chunk": "text"}
    )

    final_entities = cast(pd.DataFrame, others[0])
    final_relationships = cast(pd.DataFrame, others[1])
    entity_join = _entities(final_entities)
    relationship_join = _relationships(final_relationships)

    entity_joined = _join(selected, entity_join)
    relationship_joined = _join(entity_joined, relationship_join)
    final_joined = relationship_joined

    if covariates_enabled:
        final_covariates = cast(pd.DataFrame, others[2])
        covariate_join = _covariates(final_covariates)
        final_joined = _join(relationship_joined, covariate_join)

    aggregated = final_joined.groupby("id", sort=False).agg("first").reset_index()

    return create_verb_result(cast(Table, aggregated))


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
        left_on="id",
        right_on="id",
        how="left",
        suffixes=["_1", "_2"],
    )
