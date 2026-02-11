# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging
from dataclasses import asdict

import pandas as pd
from graphrag_input import InputReader, create_input_reader

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """Load and parse input documents into a standard format."""
    input_reader = create_input_reader(config.input, context.input_storage)

    output = await load_input_documents(input_reader)

    if len(output) == 0:
        msg = "Error reading documents, please see logs."
        logger.error(msg)
        raise ValueError(msg)

    logger.info("Final # of rows loaded: %s", len(output))
    context.stats.num_documents = len(output)

    await context.output_table_provider.write_dataframe("documents", output)

    return WorkflowFunctionOutput(result=output)


async def load_input_documents(input_reader: InputReader) -> pd.DataFrame:
    """Load and parse input documents into a standard format."""
    documents = [asdict(doc) async for doc in input_reader]
    documents = pd.DataFrame(documents)
    documents["human_readable_id"] = documents.index
    if "raw_data" not in documents.columns:
        documents["raw_data"] = pd.Series(dtype="object")
    return documents
