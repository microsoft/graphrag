# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

import pandas as pd

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.input.factory import InputReaderFactory
from graphrag.index.input.input_reader import InputReader
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.utils.storage import write_table_to_storage

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """Load and parse input documents into a standard format."""
    input_reader = InputReaderFactory().create(
        config.input.file_type,
        {"storage": context.input_storage, "config": config.input},
    )

    output = await load_input_documents(input_reader)

    logger.info("Final # of rows loaded: %s", len(output))
    context.stats.num_documents = len(output)

    await write_table_to_storage(output, "documents", context.output_storage)

    return WorkflowFunctionOutput(result=output)


async def load_input_documents(input_reader: InputReader) -> pd.DataFrame:
    """Load and parse input documents into a standard format."""
    return await input_reader.read_files()
