# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""join_text_units verb (subtask)."""

from typing import Any, cast

from datashaper.engine.verbs.verb_input import VerbInput
from datashaper.engine.verbs.verbs_mapping import verb
from datashaper.table_store.types import Table, VerbResult, create_verb_result

from graphrag.index.verbs.overrides.aggregate import aggregate_df


@verb(name="join_text_units", treats_input_tables_as_immutable=True)
def join_text_units(
    input: VerbInput,
    select_columns: list[str],
    unroll_column: str,
    aggregate_aggregations: list[dict[str, Any]],
    aggregate_groupby: list[str] | None = None,
    final_select_columns: list[str] | None = None,
    **_kwargs: dict,
) -> VerbResult:
    """Subtask to select and unroll items using an id."""
    table = input.get_input()
    selected = cast(Table, table[select_columns])
    unrolled = selected.explode(unroll_column).reset_index(drop=True)
    aggregated = aggregate_df(unrolled, aggregate_aggregations, aggregate_groupby)
    if final_select_columns is not None:
        aggregated = cast(Table, aggregated[final_select_columns])
    return create_verb_result(aggregated)
