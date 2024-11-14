# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from datashaper import DEFAULT_INPUT_NAME

from graphrag.index.config.workflow import PipelineWorkflowConfig, PipelineWorkflowStep

workflow_name = "create_final_documents"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the final documents table.

    ## Dependencies
    * `workflow:create_base_text_units`
    """
    document_attribute_columns = config.get("document_attribute_columns", None)
    return [
        {
            "verb": "create_final_documents",
            "args": {"document_attribute_columns": document_attribute_columns},
            "input": {
                "source": DEFAULT_INPUT_NAME,
                "text_units": "workflow:create_base_text_units",
            },
        },
    ]
