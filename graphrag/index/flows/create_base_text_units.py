# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform base text_units."""

from dataclasses import dataclass
from typing import Any, cast

import pandas as pd
from datashaper import (
    FieldAggregateOperation,
    Progress,
    VerbCallbacks,
    aggregate_operation_mapping,
)

from graphrag.config.models.chunking_config import ChunkStrategyType
from graphrag.index.operations.chunk_text.chunk_text import chunk_text
from graphrag.index.utils.hashing import gen_sha512_hash


def create_base_text_units(
    documents: pd.DataFrame,
    callbacks: VerbCallbacks,
    group_by_columns: list[str],
    size: int,
    overlap: int,
    encoding_model: str,
    strategy: ChunkStrategyType,
) -> pd.DataFrame:
    """All the steps to transform base text_units."""
    sort = documents.sort_values(by=["id"], ascending=[True])

    sort["text_with_ids"] = list(
        zip(*[sort[col] for col in ["id", "text"]], strict=True)
    )

    callbacks.progress(Progress(percent=0))

    aggregated = _aggregate_df(
        sort,
        groupby=[*group_by_columns] if len(group_by_columns) > 0 else None,
        aggregations=[
            {
                "column": "text_with_ids",
                "operation": "array_agg",
                "to": "texts",
            }
        ],
    )

    callbacks.progress(Progress(percent=1))

    aggregated["chunks"] = chunk_text(
        aggregated,
        column="texts",
        size=size,
        overlap=overlap,
        encoding_model=encoding_model,
        strategy=strategy,
        callbacks=callbacks,
    )

    aggregated = cast("pd.DataFrame", aggregated[[*group_by_columns, "chunks"]])
    aggregated = aggregated.explode("chunks")
    aggregated.rename(
        columns={
            "chunks": "chunk",
        },
        inplace=True,
    )
    aggregated["id"] = aggregated.apply(
        lambda row: gen_sha512_hash(row, ["chunk"]), axis=1
    )
    aggregated[["document_ids", "chunk", "n_tokens"]] = pd.DataFrame(
        aggregated["chunk"].tolist(), index=aggregated.index
    )
    # rename for downstream consumption
    aggregated.rename(columns={"chunk": "text"}, inplace=True)

    return cast(
        "pd.DataFrame", aggregated[aggregated["text"].notna()].reset_index(drop=True)
    )


# TODO: would be nice to inline this completely in the main method with pandas
def _aggregate_df(
    input: pd.DataFrame,
    aggregations: list[dict[str, Any]],
    groupby: list[str] | None = None,
) -> pd.DataFrame:
    """Aggregate method definition."""
    aggregations_to_apply = _load_aggregations(aggregations)
    df_aggregations = {
        agg.column: _get_pandas_agg_operation(agg)
        for agg in aggregations_to_apply.values()
    }
    if groupby is None:
        output_grouped = input.groupby(lambda _x: True)
    else:
        output_grouped = input.groupby(groupby, sort=False)
    output = cast("pd.DataFrame", output_grouped.agg(df_aggregations))
    output.rename(
        columns={agg.column: agg.to for agg in aggregations_to_apply.values()},
        inplace=True,
    )
    output.columns = [agg.to for agg in aggregations_to_apply.values()]
    return output.reset_index()


@dataclass
class Aggregation:
    """Aggregation class method definition."""

    column: str | None
    operation: str
    to: str

    # Only useful for the concat operation
    separator: str | None = None


def _get_pandas_agg_operation(agg: Aggregation) -> Any:
    if agg.operation == "string_concat":
        return (agg.separator or ",").join
    return aggregate_operation_mapping[FieldAggregateOperation(agg.operation)]


def _load_aggregations(
    aggregations: list[dict[str, Any]],
) -> dict[str, Aggregation]:
    return {
        aggregation["column"]: Aggregation(
            aggregation["column"], aggregation["operation"], aggregation["to"]
        )
        for aggregation in aggregations
    }
