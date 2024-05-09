# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'Aggregation' model."""

# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
from dataclasses import dataclass
from typing import Any, cast

import pandas as pd
from datashaper import (
    FieldAggregateOperation,
    Progress,
    TableContainer,
    VerbCallbacks,
    VerbInput,
    aggregate_operation_mapping,
    verb,
)

ARRAY_AGGREGATIONS = [
    FieldAggregateOperation.ArrayAgg,
    FieldAggregateOperation.ArrayAggDistinct,
]


# TODO: This thing is kinda gross
# Also, it diverges from the original aggregate verb, since it doesn't support the same syntax
@verb(name="aggregate_override")
def aggregate(
    input: VerbInput,
    callbacks: VerbCallbacks,
    aggregations: list[dict[str, Any]],
    groupby: list[str] | None = None,
    **_kwargs: dict,
) -> TableContainer:
    """Aggregate method definition."""
    aggregations_to_apply = _load_aggregations(aggregations)
    df_aggregations = {
        agg.column: _get_pandas_agg_operation(agg)
        for agg in aggregations_to_apply.values()
    }
    input_table = input.get_input()
    callbacks.progress(Progress(percent=0))

    if groupby is None:
        output_grouped = input_table.groupby(lambda _x: True)
    else:
        output_grouped = input_table.groupby(groupby, sort=False)
    output = cast(pd.DataFrame, output_grouped.agg(df_aggregations))
    output.rename(
        columns={agg.column: agg.to for agg in aggregations_to_apply.values()},
        inplace=True,
    )
    output.columns = [agg.to for agg in aggregations_to_apply.values()]

    callbacks.progress(Progress(percent=1))

    return TableContainer(table=output.reset_index())


@dataclass
class Aggregation:
    """Aggregation class method definition."""

    column: str | None
    operation: str
    to: str

    # Only useful for the concat operation
    separator: str | None = None


def _get_pandas_agg_operation(agg: Aggregation) -> Any:
    # TODO: Merge into datashaper
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
