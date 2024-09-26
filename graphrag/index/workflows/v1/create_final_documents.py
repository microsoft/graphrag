# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from graphrag.index.config import PipelineWorkflowConfig, PipelineWorkflowStep

workflow_name = "create_final_documents"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the final documents table.

    ## Dependencies
    * `workflow:create_base_documents`
    """
    base_text_embed = config.get("text_embed", {})
    document_raw_content_embed_config = config.get(
        "document_raw_content_embed", base_text_embed
    )
    skip_raw_content_embedding = config.get("skip_raw_content_embedding", False)
    return [
        {
            "verb": "create_final_documents",
            "args": {
                "columns": {"text_units": "text_unit_ids"},
                "skip_embedding": skip_raw_content_embedding,
                "text_embed": document_raw_content_embed_config,
            },
            "input": {"source": "workflow:create_base_documents"},
        },
    ]
