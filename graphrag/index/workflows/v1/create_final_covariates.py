# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from datashaper import AsyncType

from graphrag.index.config import PipelineWorkflowConfig, PipelineWorkflowStep

workflow_name = "create_final_covariates"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the final covariates table.

    ## Dependencies
    * `workflow:create_base_text_units`
    * `workflow:create_base_extracted_entities`
    """
    claim_extract_config = config.get("claim_extract", {})

    input = {"source": "workflow:create_base_text_units"}

    return [
        {
            "verb": "extract_covariates",
            "args": {
                "column": config.get("chunk_column", "chunk"),
                "id_column": config.get("chunk_id_column", "chunk_id"),
                "resolved_entities_column": "resolved_entities",
                "covariate_type": "claim",
                "async_mode": config.get("async_mode", AsyncType.AsyncIO),
                **claim_extract_config,
            },
            "input": input,
        },
        {
            "verb": "window",
            "args": {"to": "id", "operation": "uuid", "column": "covariate_type"},
        },
        {
            "verb": "genid",
            "args": {
                "to": "human_readable_id",
                "method": "increment",
            },
        },
        {
            "verb": "convert",
            "args": {
                "column": "human_readable_id",
                "type": "string",
                "to": "human_readable_id",
            },
        },
        {
            "verb": "rename",
            "args": {
                "columns": {
                    "chunk_id": "text_unit_id",
                }
            },
        },
        {
            "verb": "select",
            "args": {
                "columns": [
                    "id",
                    "human_readable_id",
                    "covariate_type",
                    "type",
                    "description",
                    "subject_id",
                    "subject_type",
                    "object_id",
                    "object_type",
                    "status",
                    "start_date",
                    "end_date",
                    "source_text",
                    "text_unit_id",
                    "document_ids",
                    "n_tokens",
                ]
            },
        },
    ]
