# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

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
    * `workflow:create_base_document_nodes`
    """
    text_embed_config = config.get("text_embed", {})
    skip_raw_content_embedding = config.get("skip_raw_content_embedding", False)
    result = [
        {
            "verb": "rename",
            "args": {"columns": {"text_units": "text_unit_ids"}},
            "input": {"source": "workflow:create_base_documents"},
        }
    ]

    if not skip_raw_content_embedding:
        result.append({
            "verb": "text_embed",
            "args": {
                "column": "raw_content",
                "to": "raw_content_embedding",
                **text_embed_config,
            },
        })

    return result
