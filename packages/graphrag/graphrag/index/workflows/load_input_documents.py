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
    logger.info("Workflow started: load_input_documents")
    input_reader = create_input_reader(config.input, context.input_storage)

    document_count = await load_input_documents_streaming(
        input_reader, context.output_table_provider
    )

    if document_count == 0:
        msg = "Error reading documents, please see logs."
        logger.error(msg)
        raise ValueError(msg)

    logger.info("Final # of rows loaded: %s", document_count)
    context.stats.num_documents = document_count

    # Read back for return value to maintain workflow compatibility
    output = await context.output_table_provider.read_dataframe("documents")
    logger.info("Workflow completed: load_input_documents")
    return WorkflowFunctionOutput(result=output)


async def load_input_documents_streaming(
    input_reader: InputReader, table_provider
) -> int:
    """Load and parse input documents into storage using streaming writes.
    
    This method loads documents from the input reader and writes them
    row-by-row to the table provider, reducing memory pressure for large
    document sets.
    
    Args
    ----
        input_reader: InputReader
            Reader for loading input documents.
        table_provider: TableProvider
            Table provider for streaming document writes.
    
    Returns
    -------
        int:
            Number of documents loaded.
    """
    # Read all documents from input reader
    # Note: InputReader.read_files() currently returns a list, not a generator
    # Future optimization: modify InputReader to yield documents one at a time
    documents = await input_reader.read_files()

    logger.info("Writing %d documents to storage using streaming...", len(documents))

    # Stream documents to table storage
    async with table_provider.open("documents") as doc_table:
        for i, doc in enumerate(documents):
            # Convert TextDocument dataclass to dict
            doc_dict = asdict(doc)
            await doc_table.write(doc_dict)

            if (i + 1) % 100 == 0:
                logger.info("Streamed %d/%d documents...", i + 1, len(documents))

    logger.info("Successfully streamed %d documents to storage", len(documents))
    return len(documents)


async def load_input_documents(input_reader: InputReader) -> pd.DataFrame:
    """Load and parse input documents into a standard format.
    
    DEPRECATED: Use load_input_documents_streaming for memory-efficient loading.
    This method is kept for backward compatibility.
    """
    return pd.DataFrame(await input_reader.read_files())
