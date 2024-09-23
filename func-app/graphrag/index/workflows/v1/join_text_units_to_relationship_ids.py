# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from graphrag.index.config import PipelineWorkflowConfig, PipelineWorkflowStep

workflow_name = "join_text_units_to_relationship_ids"


def build_steps(
    _config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create a join table from text unit ids to relationship ids.

    ## Dependencies
    * `workflow:create_final_relationships
    """
    return [
        {
            "verb": "select",
            "args": {"columns": ["id", "text_unit_ids"]},
            "input": {"source": "workflow:create_final_relationships"},
        },
        {
            "verb": "unroll",
            "args": {
                "column": "text_unit_ids",
            },
        },
        {
            "verb": "aggregate_override",
            "args": {
                "groupby": ["text_unit_ids"],
                "aggregations": [
                    {
                        "column": "id",
                        "operation": "array_agg_distinct",
                        "to": "relationship_ids",
                    },
                    {
                        "column": "text_unit_ids",
                        "operation": "any",
                        "to": "id",
                    },
                ],
            },
        },
        {
            "id": "text_unit_id_to_relationship_ids",
            "verb": "select",
            "args": {"columns": ["id", "relationship_ids"]},
        },
    ]
