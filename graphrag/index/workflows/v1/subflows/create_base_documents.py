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


@verb(name="create_base_documents", treats_input_tables_as_immutable=True)
def create_base_documents(
    input: VerbInput,
    document_attribute_columns: list[str] | None = None,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform base documents."""
    source = cast(pd.DataFrame, input.get_input())
    text_units = cast(pd.DataFrame, input.get_others()[0])

    text_units = (
        text_units.explode("document_ids")
        .loc[:, ["id", "document_ids", "text"]]
        .rename(
            columns={
                "document_ids": "chunk_doc_id",
                "id": "chunk_id",
                "text": "chunk_text",
            }
        )
    )

    joined = text_units.merge(
        source,
        left_on="chunk_doc_id",
        right_on="id",
        how="inner",
        copy=False,
    )

    docs_with_text_units = joined.groupby("id", sort=False).agg(
        text_units=("chunk_id", list)
    )

    rejoined = docs_with_text_units.merge(
        source,
        on="id",
        how="right",
        copy=False,
    ).reset_index(drop=True)

    rejoined.rename(columns={"text": "raw_content"}, inplace=True)
    rejoined["id"] = rejoined["id"].astype(str)

    # Convert attribute columns to strings and collapse them into a JSON object
    if document_attribute_columns:
        # Convert all specified columns to string at once
        rejoined[document_attribute_columns] = rejoined[
            document_attribute_columns
        ].astype(str)

        # Collapse the document_attribute_columns into a single JSON object column
        rejoined["attributes"] = rejoined[document_attribute_columns].to_dict(
            orient="records"
        )

        # Drop the original attribute columns after collapsing them
        rejoined.drop(columns=document_attribute_columns, inplace=True)

    return create_verb_result(
        cast(
            Table,
            rejoined,
        )
    )
