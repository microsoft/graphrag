# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import pandas as pd

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.context import PipelineRunContext
from graphrag.index.typing import WorkflowFunctionOutput
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage


async def run_workflow(
    _config: GraphRagConfig,
    context: PipelineRunContext,
    _callbacks: WorkflowCallbacks,
) -> WorkflowFunctionOutput:
    """All the steps to transform final documents."""
    documents = await load_table_from_storage("documents", context.storage)
    text_units = await load_table_from_storage("text_units", context.storage)

    output = create_final_documents(documents, text_units)

    await write_table_to_storage(output, "documents", context.storage)

    return WorkflowFunctionOutput(result=output, config=None)


def create_final_documents(
    documents: pd.DataFrame, text_units: pd.DataFrame
) -> pd.DataFrame:
    """All the steps to transform final documents."""
    exploded = (
        text_units.explode("document_ids")
        .loc[:, ["id", "document_ids", "text"]]
        .rename(
            columns={
                "document_ids": "chunk_doc_id",
                "id": "chunk_id",
                "text": "chunk_text",
            }
        )
    )

    joined = exploded.merge(
        documents,
        left_on="chunk_doc_id",
        right_on="id",
        how="inner",
        copy=False,
    )

    docs_with_text_units = joined.groupby("id", sort=False).agg(
        text_unit_ids=("chunk_id", list)
    )

    rejoined = docs_with_text_units.merge(
        documents,
        on="id",
        how="right",
        copy=False,
    ).reset_index(drop=True)

    rejoined["id"] = rejoined["id"].astype(str)
    rejoined["human_readable_id"] = rejoined.index + 1

    # set the final column order, but adjust for metadata
    core_columns = [
        "id",
        "human_readable_id",
        "title",
        "text",
        "text_unit_ids",
        "creation_date",
    ]
    final_columns = [column for column in core_columns if column in rejoined.columns]
    if "metadata" in rejoined.columns:
        final_columns.append("metadata")

    return rejoined.loc[:, final_columns]
