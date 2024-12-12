# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from typing import TYPE_CHECKING, cast

from datashaper import (
    Table,
    VerbInput,
    VerbResult,
    create_verb_result,
    verb,
)

from graphrag.index.config.workflow import PipelineWorkflowConfig, PipelineWorkflowStep
from graphrag.index.flows.create_final_text_units import (
    create_final_text_units,
)
from graphrag.index.utils.ds_util import get_named_input_table, get_required_input_table
from graphrag.storage.pipeline_storage import PipelineStorage

if TYPE_CHECKING:
    import pandas as pd

workflow_name = "create_final_text_units"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the final text-units table.

    ## Dependencies
    * `workflow:create_base_text_units`
    * `workflow:create_final_entities`
    * `workflow:create_final_communities`
    """
    covariates_enabled = config.get("covariates_enabled", False)

    input = {
        "source": "workflow:create_base_text_units",
        "entities": "workflow:create_final_entities",
        "relationships": "workflow:create_final_relationships",
    }

    if covariates_enabled:
        input["covariates"] = "workflow:create_final_covariates"

    return [
        {
            "verb": workflow_name,
            "args": {},
            "input": input,
        },
    ]


@verb(name=workflow_name, treats_input_tables_as_immutable=True)
async def workflow(
    input: VerbInput,
    runtime_storage: PipelineStorage,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform the text units."""
    text_units = await runtime_storage.get("base_text_units")
    final_entities = cast(
        "pd.DataFrame", get_required_input_table(input, "entities").table
    )
    final_relationships = cast(
        "pd.DataFrame", get_required_input_table(input, "relationships").table
    )
    final_covariates = get_named_input_table(input, "covariates")

    if final_covariates:
        final_covariates = cast("pd.DataFrame", final_covariates.table)

    output = create_final_text_units(
        text_units,
        final_entities,
        final_relationships,
        final_covariates,
    )

    return create_verb_result(cast("Table", output))
