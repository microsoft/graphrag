# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform the text units."""

from typing import cast

import pandas as pd
from datashaper import (
    Table,
    VerbInput,
    VerbResult,
    create_verb_result,
    verb,
)

from graphrag.index.flows.create_final_text_units import (
    create_final_text_units as create_final_text_units_flow,
)
from graphrag.index.storage.pipeline_storage import PipelineStorage
from graphrag.index.utils.ds_util import get_named_input_table, get_required_input_table


@verb(name="create_final_text_units", treats_input_tables_as_immutable=True)
async def create_final_text_units(
    input: VerbInput,
    runtime_storage: PipelineStorage,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform the text units."""
    text_units = await runtime_storage.get("base_text_units")
    final_entities = cast(
        pd.DataFrame, get_required_input_table(input, "entities").table
    )
    final_relationships = cast(
        pd.DataFrame, get_required_input_table(input, "relationships").table
    )
    final_covariates = get_named_input_table(input, "covariates")

    if final_covariates:
        final_covariates = cast(pd.DataFrame, final_covariates.table)

    output = create_final_text_units_flow(
        text_units,
        final_entities,
        final_relationships,
        final_covariates,
    )

    return create_verb_result(cast(Table, output))
