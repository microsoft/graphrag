# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging
from dataclasses import asdict

import pandas as pd
from graphrag_input import InputReader, create_input_reader
from graphrag_storage.tables.table import Table

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

    async with (
        context.output_table_provider.open("documents") as documents_table,
    ):
        sample, total_count = await load_input_documents(input_reader, documents_table)

        if total_count == 0:
            msg = "Error reading documents, please see logs."
            logger.error(msg)
            raise ValueError(msg)

        logger.info("Final # of rows loaded: %s", total_count)
        context.stats.num_documents = total_count

    return WorkflowFunctionOutput(result=sample)


async def load_input_documents(
    input_reader: InputReader, documents_table: Table, sample_size: int = 5
) -> tuple[pd.DataFrame, int]:
    """Load and parse input documents into a standard format."""
    sample: list[dict] = []
    idx = 0

    async for doc in input_reader:
        row = asdict(doc)
        row["human_readable_id"] = idx
        if "raw_data" not in row:
            row["raw_data"] = None
        await documents_table.write(row)
        if len(sample) < sample_size:
            sample.append(row)
        idx += 1

    return pd.DataFrame(sample), idx
