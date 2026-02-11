# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

import pandas as pd

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.data_model.data_reader import DataReader
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
    reader = DataReader(context.output_table_provider)
    documents = await reader.documents()
    text_units = await reader.text_units()

    output = create_final_documents(documents, text_units)

    await context.output_table_provider.write_dataframe("documents", output)

    logger.info("Workflow completed: create_final_documents")
    return WorkflowFunctionOutput(result=output)


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

    return rejoined.loc[:, DOCUMENTS_FINAL_COLUMNS]
