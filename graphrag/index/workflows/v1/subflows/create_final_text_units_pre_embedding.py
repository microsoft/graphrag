# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform before we embed the text units."""

from typing import cast

import pandas as pd
from datashaper.engine.verbs.verb_input import VerbInput
from datashaper.engine.verbs.verbs_mapping import verb
from datashaper.table_store.types import Table, VerbResult, create_verb_result
from pandas._typing import Suffixes

from graphrag.index.verbs.overrides.aggregate import aggregate_df


@verb(
    name="create_final_text_units_pre_embedding", treats_input_tables_as_immutable=True
)
def create_final_text_units_pre_embedding(
    input: VerbInput,
    covariates_enabled: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform before we embed the text units."""
    table = input.get_input()
    others = input.get_others()

    selected = cast(Table, table[["id", "chunk", "document_ids", "n_tokens"]]).rename(
        columns={"chunk": "text"}
    )

    final_entities = others[0]
    final_relationships = others[1]
    entity_join = _entities(final_entities)
    relationship_join = _relationships(final_relationships)

    entity_joined = _join(selected, entity_join)
    relationship_joined = _join(entity_joined, relationship_join)
    final_joined = relationship_joined

    if covariates_enabled:
        final_covariates = others[2]
        covariate_join = _covariates(final_covariates)
        final_joined = _join(relationship_joined, covariate_join)

    aggregated = aggregate_df(
        final_joined,
        [
            {
                "column": "text",
                "operation": "any",
                "to": "text",
            },
            {
                "column": "n_tokens",
                "operation": "any",
                "to": "n_tokens",
            },
            {
                "column": "document_ids",
                "operation": "any",
                "to": "document_ids",
            },
            {
                "column": "entity_ids",
                "operation": "any",
                "to": "entity_ids",
            },
            {
                "column": "relationship_ids",
                "operation": "any",
                "to": "relationship_ids",
            },
            *(
                []
                if not covariates_enabled
                else [
                    {
                        "column": "covariate_ids",
                        "operation": "any",
                        "to": "covariate_ids",
                    }
                ]
            ),
        ],
        ["id"],
    )

    return create_verb_result(aggregated)


def _entities(table):
    selected = cast(Table, table[["id", "text_unit_ids"]])
    unrolled = selected.explode("text_unit_ids").reset_index(drop=True)
    return aggregate_df(
        unrolled,
        [
            {
                "column": "id",
                "operation": "array_agg_distinct",
                "to": "entity_ids",
            },
            {
                "column": "text_unit_ids",
                "operation": "any",
                "to": "id",
            },
        ],
        ["text_unit_ids"],
    )


def _relationships(table):
    selected = cast(Table, table[["id", "text_unit_ids"]])
    unrolled = selected.explode("text_unit_ids").reset_index(drop=True)
    aggregated = aggregate_df(
        unrolled,
        [
            {
                "column": "id",
                "operation": "array_agg_distinct",
                "to": "relationship_ids",
            },
            {
                "column": "text_unit_ids",
                "operation": "any",
                "to": "id",
            },
        ],
        ["text_unit_ids"],
    )
    return aggregated[["id", "relationship_ids"]]


def _covariates(table):
    selected = cast(Table, table[["id", "text_unit_id"]])
    return aggregate_df(
        selected,
        [
            {
                "column": "id",
                "operation": "array_agg_distinct",
                "to": "covariate_ids",
            },
            {
                "column": "text_unit_id",
                "operation": "any",
                "to": "id",
            },
        ],
        ["text_unit_id"],
    )


def _join(left, right):
    return __clean_result(
        left.merge(
            right,
            left_on="id",
            right_on="id",
            how="left",
            suffixes=cast(Suffixes, ["_1", "_2"]),
            indicator=True,
        )
    )


def __clean_result(result: pd.DataFrame) -> pd.DataFrame:
    result = cast(
        pd.DataFrame,
        pd.concat([
            result[result["_merge"] == "both"],
            result[result["_merge"] == "left_only"],
            result[result["_merge"] == "right_only"],
        ]),
    )
    return result.drop("_merge", axis=1)
