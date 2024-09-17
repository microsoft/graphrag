# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform before we embed the text units."""

from typing import cast

from datashaper.engine.verbs.verb_input import VerbInput
from datashaper.engine.verbs.verbs_mapping import verb
from datashaper.table_store.types import Table, VerbResult, create_verb_result

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

    aggregated = _final_aggregation(final_joined, covariates_enabled)

    return create_verb_result(aggregated)


def _final_aggregation(table, covariates_enabled):
    aggregations = [
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
    ]
    if covariates_enabled:
        aggregations.append({
            "column": "covariate_ids",
            "operation": "any",
            "to": "covariate_ids",
        })
    return aggregate_df(
        table,
        aggregations,
        ["id"],
    )


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
    return left.merge(
        right,
        left_on="id",
        right_on="id",
        how="left",
        suffixes=["_1", "_2"],
    )
