# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform base documents."""

from typing import cast

import pandas as pd
from datashaper import (
    Table,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.verbs.overrides.aggregate import aggregate_df


@verb(name="create_base_documents", treats_input_tables_as_immutable=True)
def create_base_documents(
    input: VerbInput,
    document_attribute_columns: list[str] | None = None,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform base documents."""
    source = cast(pd.DataFrame, input.get_input())
    text_units = cast(pd.DataFrame, input.get_others()[0])

    text_units = cast(
        pd.DataFrame, text_units.explode("document_ids")[["id", "document_ids", "text"]]
    )
    text_units.rename(
        columns={
            "document_ids": "chunk_doc_id",
            "id": "chunk_id",
            "text": "chunk_text",
        },
        inplace=True,
    )

    joined = text_units.merge(
        source,
        left_on="chunk_doc_id",
        right_on="id",
        how="inner",
    )

    docs_with_text_units = aggregate_df(
        joined,
        groupby=["id"],
        aggregations=[
            {
                "column": "chunk_id",
                "operation": "array_agg",
                "to": "text_units",
            }
        ],
    )

    rejoined = docs_with_text_units.merge(
        source,
        on="id",
        how="right",
    )
    rejoined.rename(columns={"text": "raw_content"}, inplace=True)
    rejoined["id"] = rejoined["id"].astype(str)

    # attribute columns are converted to strings and then collapsed into a single json object
    if document_attribute_columns:
        for column in document_attribute_columns:
            rejoined[column] = rejoined[column].astype(str)
        rejoined["attributes"] = rejoined[document_attribute_columns].apply(
            lambda row: {**row},
            axis=1,
        )
        rejoined.drop(columns=document_attribute_columns, inplace=True)
        rejoined.reset_index()

    return create_verb_result(
        cast(
            Table,
            rejoined,
        )
    )
