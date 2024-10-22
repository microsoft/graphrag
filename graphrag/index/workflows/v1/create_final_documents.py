# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from datashaper import DEFAULT_INPUT_NAME

from graphrag.index.config import PipelineWorkflowConfig, PipelineWorkflowStep

workflow_name = "create_final_documents"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the final documents table.

    ## Dependencies
    * `workflow:create_final_text_units`
    """
    base_text_embed = config.get("text_embed", {})
    document_raw_content_embed_config = config.get(
        "document_raw_content_embed", base_text_embed
    )
    skip_raw_content_embedding = config.get("skip_raw_content_embedding", False)
    document_attribute_columns = config.get("document_attribute_columns", [])
    return [
        {
            "verb": "create_final_documents",
            "args": {
                "document_attribute_columns": document_attribute_columns,
                "raw_content_text_embed": document_raw_content_embed_config
                if not skip_raw_content_embedding
                else None,
            },
            "input": {
                "source": DEFAULT_INPUT_NAME,
                "text_units": "workflow:create_final_text_units",
            },
        },
    ]
