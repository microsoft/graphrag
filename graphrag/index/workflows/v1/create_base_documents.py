# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from datashaper import DEFAULT_INPUT_NAME

from graphrag.index.config import PipelineWorkflowConfig, PipelineWorkflowStep

workflow_name = "create_base_documents"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the documents table.

    ## Dependencies
    * `workflow:create_final_text_units`
    """
    document_attribute_columns = config.get("document_attribute_columns", [])
    return [
        {
            "verb": "create_base_documents",
            "input": {
                "source": DEFAULT_INPUT_NAME,
                "others": ["workflow:create_final_text_units"],
            },
        },
        *[
            {
                "verb": "convert",
                "args": {
                    "column": column,
                    "to": column,
                    "type": "string",
                },
            }
            for column in document_attribute_columns
        ],
        {
            "verb": "merge_override",
            "enabled": len(document_attribute_columns) > 0,
            "args": {
                "columns": document_attribute_columns,
                "strategy": "json",
                "to": "attributes",
            },
        },
        {"verb": "convert", "args": {"column": "id", "to": "id", "type": "string"}},
    ]
