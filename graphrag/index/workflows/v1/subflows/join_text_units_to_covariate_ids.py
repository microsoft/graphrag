# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""join_text_units_to_covariate_ids verb (subtask)."""

from typing import Any, cast

from datashaper.engine.verbs.verb_input import VerbInput
from datashaper.engine.verbs.verbs_mapping import verb
from datashaper.table_store.types import Table, VerbResult, create_verb_result

from graphrag.index.verbs.overrides.aggregate import aggregate_df


@verb(name="join_text_units_to_covariate_ids", treats_input_tables_as_immutable=True)
def join_text_units_to_covariate_ids(
    input: VerbInput,
    select_columns: list[str],
    aggregate_aggregations: list[dict[str, Any]],
    aggregate_groupby: list[str] | None = None,
    **_kwargs: dict,
) -> VerbResult:
    """Subtask to select and unroll items using an id."""
    table = input.get_input()
    selected = cast(Table, table[select_columns])
    aggregated = aggregate_df(selected, aggregate_aggregations, aggregate_groupby)
    return create_verb_result(aggregated)
