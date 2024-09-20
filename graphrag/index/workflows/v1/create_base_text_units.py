# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from datashaper import DEFAULT_INPUT_NAME

from graphrag.index.config import PipelineWorkflowConfig, PipelineWorkflowStep

workflow_name = "create_base_text_units"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the base table for text units.

    ## Dependencies
    None
    """
    chunk_column_name = config.get("chunk_column", "chunk")
    chunk_by_columns = config.get("chunk_by", []) or []
    n_tokens_column_name = config.get("n_tokens_column", "n_tokens")
    text_chunk = config.get("text_chunk", {})
    return [
        {
            "verb": "create_base_text_units",
            "args": {
                "chunk_column_name": chunk_column_name,
                "n_tokens_column_name": n_tokens_column_name,
                "chunk_by_columns": chunk_by_columns,
                **text_chunk,
            },
            "input": {"source": DEFAULT_INPUT_NAME},
        },
    ]
