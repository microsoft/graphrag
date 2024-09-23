# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform base text_units."""

from typing import Any, cast

import pandas as pd
from datashaper import (
    Table,
    VerbCallbacks,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.verbs.genid import genid_df
from graphrag.index.verbs.overrides.aggregate import aggregate_df
from graphrag.index.verbs.text.chunk.text_chunk import chunk_df


@verb(name="create_base_text_units", treats_input_tables_as_immutable=True)
def create_base_text_units(
    input: VerbInput,
    callbacks: VerbCallbacks,
    chunk_column_name: str,
    n_tokens_column_name: str,
    chunk_by_columns: list[str],
    strategy: dict[str, Any] | None = None,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform base text_units."""
    table = cast(pd.DataFrame, input.get_input())

    sort = table.sort_values(by=["id"], ascending=[True])

    sort["text_with_ids"] = list(
        zip(*[sort[col] for col in ["id", "text"]], strict=True)
    )

    aggregated = aggregate_df(
        sort,
        groupby=[*chunk_by_columns] if len(chunk_by_columns) > 0 else None,
        aggregations=[
            {
                "column": "text_with_ids",
                "operation": "array_agg",
                "to": "texts",
            }
        ],
    )

    chunked = chunk_df(
        aggregated,
        column="texts",
        to="chunks",
        callbacks=callbacks,
        strategy=strategy,
    )

    chunked = cast(pd.DataFrame, chunked[[*chunk_by_columns, "chunks"]])
    chunked = chunked.explode("chunks")
    chunked.rename(
        columns={
            "chunks": chunk_column_name,
        },
        inplace=True,
    )

    chunked = genid_df(
        chunked, to="chunk_id", method="md5_hash", hash=[chunk_column_name]
    )

    chunked[["document_ids", chunk_column_name, n_tokens_column_name]] = pd.DataFrame(
        chunked[chunk_column_name].tolist(), index=chunked.index
    )
    chunked["id"] = chunked["chunk_id"]

    filtered = chunked[chunked[chunk_column_name].notna()].reset_index(drop=True)

    return create_verb_result(
        cast(
            Table,
            filtered,
        )
    )
