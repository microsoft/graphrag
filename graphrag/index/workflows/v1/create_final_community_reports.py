# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from typing import TYPE_CHECKING, cast

from datashaper import (
    AsyncType,
    Table,
    VerbCallbacks,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.cache.pipeline_cache import PipelineCache
from graphrag.index.config.workflow import PipelineWorkflowConfig, PipelineWorkflowStep
from graphrag.index.flows.create_final_community_reports import (
    create_final_community_reports,
)
from graphrag.index.utils.ds_util import get_named_input_table, get_required_input_table

if TYPE_CHECKING:
    import pandas as pd

workflow_name = "create_final_community_reports"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the final community reports table.

    ## Dependencies
    * `workflow:extract_graph`
    """
    covariates_enabled = config.get("covariates_enabled", False)
    create_community_reports_config = config.get("create_community_reports", {})
    summarization_strategy = create_community_reports_config.get("strategy")
    async_mode = create_community_reports_config.get("async_mode")
    num_threads = create_community_reports_config.get("num_threads")

    input = {
        "source": "workflow:create_final_nodes",
        "relationships": "workflow:create_final_relationships",
        "entities": "workflow:create_final_entities",
        "communities": "workflow:create_final_communities",
    }
    if covariates_enabled:
        input["covariates"] = "workflow:create_final_covariates"

    return [
        {
            "verb": workflow_name,
            "args": {
                "summarization_strategy": summarization_strategy,
                "async_mode": async_mode,
                "num_threads": num_threads,
            },
            "input": input,
        },
    ]


@verb(name=workflow_name, treats_input_tables_as_immutable=True)
async def workflow(
    input: VerbInput,
    callbacks: VerbCallbacks,
    cache: PipelineCache,
    summarization_strategy: dict,
    async_mode: AsyncType = AsyncType.AsyncIO,
    num_threads: int = 4,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform community reports."""
    nodes = cast("pd.DataFrame", input.get_input())
    edges = cast("pd.DataFrame", get_required_input_table(input, "relationships").table)
    entities = cast("pd.DataFrame", get_required_input_table(input, "entities").table)
    communities = cast(
        "pd.DataFrame", get_required_input_table(input, "communities").table
    )

    claims = get_named_input_table(input, "covariates")
    if claims:
        claims = cast("pd.DataFrame", claims.table)

    output = await create_final_community_reports(
        nodes,
        edges,
        entities,
        communities,
        claims,
        callbacks,
        cache,
        summarization_strategy,
        async_mode=async_mode,
        num_threads=num_threads,
    )

    return create_verb_result(
        cast(
            "Table",
            output,
        )
    )
