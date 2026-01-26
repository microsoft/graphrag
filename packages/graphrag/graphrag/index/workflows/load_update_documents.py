# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging

import pandas as pd
from graphrag_input.input_reader import InputReader
from graphrag_input.input_reader_factory import create_input_reader
from graphrag_storage import Storage

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
    input_reader = create_input_reader(config.input, context.input_storage)
    output = await load_update_documents(
        input_reader,
        context.previous_storage,
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
    previous_storage: Storage,
) -> pd.DataFrame:
    """Load and parse update-only input documents into a standard format."""
    input_documents = pd.DataFrame(await input_reader.read_files())
    # previous storage is the output of the previous run
    # we'll use this to diff the input from the prior
    delta_documents = await get_delta_docs(input_documents, previous_storage)
    return delta_documents.new_inputs
