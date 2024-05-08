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
            "verb": "unroll",
            "args": {"column": "document_ids"},
            "input": {"source": "workflow:create_final_text_units"},
        },
        {
            "verb": "select",
            "args": {
                # We only need the chunk id and the document id
                "columns": ["id", "document_ids", "text"]
            },
        },
        {
            "id": "rename_chunk_doc_id",
            "verb": "rename",
            "args": {
                "columns": {
                    "document_ids": "chunk_doc_id",
                    "id": "chunk_id",
                    "text": "chunk_text",
                }
            },
        },
        {
            "verb": "join",
            "args": {
                # Join the doc id from the chunk onto the original document
                "on": ["chunk_doc_id", "id"]
            },
            "input": {"source": "rename_chunk_doc_id", "others": [DEFAULT_INPUT_NAME]},
        },
        {
            "id": "docs_with_text_units",
            "verb": "aggregate_override",
            "args": {
                "groupby": ["id"],
                "aggregations": [
                    {
                        "column": "chunk_id",
                        "operation": "array_agg",
                        "to": "text_units",
                    }
                ],
            },
        },
        {
            "verb": "join",
            "args": {
                "on": ["id", "id"],
                "strategy": "right outer",
            },
            "input": {
                "source": "docs_with_text_units",
                "others": [DEFAULT_INPUT_NAME],
            },
        },
        {
            "verb": "rename",
            "args": {"columns": {"text": "raw_content"}},
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
