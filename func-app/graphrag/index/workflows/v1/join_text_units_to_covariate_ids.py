# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from graphrag.index.config import PipelineWorkflowConfig, PipelineWorkflowStep

workflow_name = "join_text_units_to_covariate_ids"


def build_steps(
    _config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the final text-units table.

    ## Dependencies
    * `workflow:create_final_covariates`
    """
    return [
        {
            "verb": "select",
            "args": {"columns": ["id", "text_unit_id"]},
            "input": {"source": "workflow:create_final_covariates"},
        },
        {
            "verb": "aggregate_override",
            "args": {
                "groupby": ["text_unit_id"],
                "aggregations": [
                    {
                        "column": "id",
                        "operation": "array_agg_distinct",
                        "to": "covariate_ids",
                    },
                    {
                        "column": "text_unit_id",
                        "operation": "any",
                        "to": "id",
                    },
                ],
            },
        },
    ]
