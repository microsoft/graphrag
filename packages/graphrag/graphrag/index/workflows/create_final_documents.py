# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

import pandas as pd

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.schemas import DOCUMENTS_FINAL_COLUMNS
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput

logger = logging.getLogger(__name__)


async def run_workflow(
    _config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """All the steps to transform final documents."""
    logger.info("Workflow started: create_final_documents")
    
    # Use streaming approach
    await create_final_documents_streaming(context.output_table_provider)

    # Read back for return value to maintain workflow compatibility
    output = await context.output_table_provider.read_dataframe("documents")
    logger.info("Workflow completed: create_final_documents")
    return WorkflowFunctionOutput(result=output)


async def create_final_documents_streaming(table_provider) -> None:
    """Transform documents using streaming to reduce memory pressure."""
    from collections import defaultdict
    
    logger.info("Building text unit lookup from text_units table...")
    
    # Build lookup: document_id -> list[text_unit_id]
    text_unit_lookup = defaultdict(list)
    text_units = await table_provider.read_dataframe("text_units")
    for _, row in text_units.iterrows():
        tu_id = row["id"]
        doc_id = row.get("document_id")
        if doc_id:
            text_unit_lookup[doc_id].append(tu_id)
    
    logger.info("Built text unit lookup with %d documents", len(text_unit_lookup))
    logger.info("Streaming documents and attaching text units...")
    
    # Stream over documents, attach text_unit_ids, and write
    row_count = 0
    async with table_provider.open("documents") as input_table:
        async with table_provider.open("documents_temp") as output_table:
            for row in input_table:
                document_id = row["id"]
                
                # Get text unit IDs for this document
                text_unit_ids = text_unit_lookup.get(document_id, [])
                
                # Build final row with all required fields
                final_row = {**row, "text_unit_ids": text_unit_ids}
                
                await output_table.write(final_row)
                row_count += 1
                
                if row_count % 100 == 0:
                    logger.info("Processed %d documents...", row_count)
    
    # Replace original with temp (read temp, delete old, write as original)
    temp_df = await table_provider.read_dataframe("documents_temp")
    await table_provider.write_dataframe("documents", temp_df)
    logger.info("Completed streaming %d documents", row_count)


def create_final_documents(
    documents: pd.DataFrame, text_units: pd.DataFrame
) -> pd.DataFrame:
    """All the steps to transform final documents."""
    renamed = text_units.loc[:, ["id", "document_id", "text"]].rename(
        columns={
            "document_id": "chunk_doc_id",
            "id": "chunk_id",
            "text": "chunk_text",
        }
    )

    joined = renamed.merge(
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
    rejoined["human_readable_id"] = rejoined.index

    if "raw_data" not in rejoined.columns:
        rejoined["raw_data"] = pd.Series(dtype="object")

    return rejoined.loc[:, DOCUMENTS_FINAL_COLUMNS]
