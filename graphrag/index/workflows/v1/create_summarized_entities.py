# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from datashaper import AsyncType

from graphrag.index.config import PipelineWorkflowConfig, PipelineWorkflowStep

workflow_name = "create_summarized_entities"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the base table for extracted entities.

    ## Dependencies
    * `workflow:create_base_text_units`
    """
    summarize_descriptions_config = config.get("summarize_descriptions", {})
    graphml_snapshot_enabled = config.get("graphml_snapshot", False) or False

    return [
        {
            "verb": "summarize_descriptions",
            "args": {
                **summarize_descriptions_config,
                "column": "entity_graph",
                "to": "entity_graph",
                "async_mode": summarize_descriptions_config.get(
                    "async_mode", AsyncType.AsyncIO
                ),
            },
            "input": {"source": "workflow:create_base_extracted_entities"},
        },
        {
            "verb": "snapshot_rows",
            "enabled": graphml_snapshot_enabled,
            "args": {
                "base_name": "summarized_graph",
                "column": "entity_graph",
                "formats": [{"format": "text", "extension": "graphml"}],
            },
        },
    ]
