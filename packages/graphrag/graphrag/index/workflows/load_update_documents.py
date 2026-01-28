# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

import pandas as pd
from graphrag_input.input_reader import InputReader
from graphrag_input.input_reader_factory import create_input_reader
from graphrag_storage.tables.table_provider import TableProvider

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.index.update.incremental_index import get_delta_docs

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """Load and parse update-only input documents into a standard format."""
    if context.previous_table_provider is None:
        msg = "previous_table_provider is required for update workflows"
        raise ValueError(msg)

    input_reader = create_input_reader(config.input, context.input_storage)
    output = await load_update_documents(
        input_reader,
        context.previous_table_provider,
    )

    logger.info("Final # of update rows loaded: %s", len(output))
    context.stats.update_documents = len(output)

    if len(output) == 0:
        logger.warning("No new update documents found.")
        return WorkflowFunctionOutput(result=None, stop=True)

    await context.output_table_provider.write_dataframe("documents", output)

    return WorkflowFunctionOutput(result=output)


async def load_update_documents(
    input_reader: InputReader,
    previous_table_provider: TableProvider,
) -> pd.DataFrame:
    """Load and parse update-only input documents into a standard format."""
    input_documents = pd.DataFrame(await input_reader.read_files())
    # previous table provider has the output of the previous run
    # we'll use this to diff the input from the prior
    delta_documents = await get_delta_docs(input_documents, previous_table_provider)
    return delta_documents.new_inputs
