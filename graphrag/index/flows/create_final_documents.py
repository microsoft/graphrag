# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final documents."""

import pandas as pd


def create_final_documents(
    documents: pd.DataFrame,
    text_units: pd.DataFrame,
    document_attribute_columns: list[str] | None = None,
) -> pd.DataFrame:
    """All the steps to transform final documents."""
    exploded = (
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

    joined = exploded.merge(
        documents,
        left_on="chunk_doc_id",
        right_on="id",
        how="inner",
        copy=False,
    )

    docs_with_text_units = joined.groupby("id", sort=False).agg(
        text_unit_ids=("chunk_id", list)
    )

    rejoined = docs_with_text_units.merge(
        documents,
        on="id",
        how="right",
        copy=False,
    ).reset_index(drop=True)

    rejoined["id"] = rejoined["id"].astype(str)
    rejoined["human_readable_id"] = rejoined.index + 1

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

    # set the final column order, but adjust for attributes
    core_columns = [
        "id",
        "human_readable_id",
        "title",
        "text",
        "text_unit_ids",
    ]
    final_columns = [column for column in core_columns if column in rejoined.columns]
    if document_attribute_columns:
        final_columns.append("attributes")

    return rejoined.loc[:, final_columns]
