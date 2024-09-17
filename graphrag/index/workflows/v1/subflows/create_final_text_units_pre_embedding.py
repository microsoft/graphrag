# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform before we embed the text units."""

import pandas as pd

from typing import Any, cast

from datashaper.engine.verbs.verb_input import VerbInput
from datashaper.engine.verbs.verbs_mapping import verb
from datashaper.table_store.types import Table, VerbResult, create_verb_result

from graphrag.index.verbs.overrides.aggregate import aggregate_df

from pandas._typing import MergeHow, Suffixes

@verb(name="create_final_text_units_pre_embedding", treats_input_tables_as_immutable=True)
def create_final_text_units_pre_embedding(
    input: VerbInput,
    covariates_enabled: bool = False,
    **_kwargs: dict,
) -> VerbResult:
    
    table = input.get_input()
    
    # initial formatting
    selected = cast(Table, table[["id", "chunk", "document_ids", "n_tokens"]]).rename(columns={"chunk": "text"})

    entity_join = input.others[0].table
    relationship_join = input.others[1].table

    entity_joined = join(selected, entity_join)
    relationship_joined = join(entity_joined, relationship_join)
    final_joined = relationship_joined

    if covariates_enabled:
        covariate_join = input.others[2].table
        final_joined = join(relationship_joined, covariate_join)

    aggregated = aggregate_df(final_joined, [
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
    ], ["id"])

    return create_verb_result(aggregated)


def join(left, right):
    return __clean_result(left.merge(
        right,
        left_on="id",
        right_on="id",
        how="left",
        suffixes=cast(Suffixes, ["_1", "_2"]),
        indicator=True,)
    )

def __clean_result(
    result: pd.DataFrame
) -> pd.DataFrame:

    result = cast(
        pd.DataFrame,
        pd.concat(
            [
                result[result["_merge"] == "both"],
                result[result["_merge"] == "left_only"],
                result[result["_merge"] == "right_only"],
            ]
        ),
    )
    return result.drop("_merge", axis=1)
