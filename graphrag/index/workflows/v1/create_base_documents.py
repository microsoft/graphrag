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
            "args": {
                "document_attribute_columns": document_attribute_columns,
            },
            "input": {
                "source": DEFAULT_INPUT_NAME,
                "others": ["workflow:create_final_text_units"],
            },
        },
    ]
