# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import json
import logging
from typing import Any, cast

import pandas as pd
from graphrag_chunking.add_metadata import add_metadata
from graphrag_chunking.chunker import Chunker
from graphrag_chunking.chunker_factory import create_chunker

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.index.utils.hashing import gen_sha512_hash
from graphrag.logger.progress import progress_ticker
from graphrag.tokenizer.get_tokenizer import get_tokenizer
from graphrag.tokenizer.tokenizer import Tokenizer
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """All the steps to transform base text_units."""
    logger.info("Workflow started: create_base_text_units")
    documents = await load_table_from_storage("documents", context.output_storage)

    tokenizer = get_tokenizer(encoding_model=config.chunking.encoding_model)
    chunker = create_chunker(config.chunking, tokenizer.encode, tokenizer.decode)
    output = create_base_text_units(
        documents,
        context.callbacks,
        tokenizer=tokenizer,
        chunker=chunker,
        prepend_metadata=config.chunking.prepend_metadata,
    )

    await write_table_to_storage(output, "text_units", context.output_storage)

    logger.info("Workflow completed: create_base_text_units")
    return WorkflowFunctionOutput(result=output)


def create_base_text_units(
    documents: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    tokenizer: Tokenizer,
    chunker: Chunker,
    prepend_metadata: bool | None = False,
) -> pd.DataFrame:
    """All the steps to transform base text_units."""
    documents.sort_values(by=["id"], ascending=[True], inplace=True)

    total_rows = len(documents)
    tick = progress_ticker(callbacks.progress, total_rows)

    # Track progress of row-wise apply operation
    logger.info("Starting chunking process for %d documents", total_rows)

    def chunker_with_logging(row: pd.Series, row_index: int) -> Any:
        row["chunks"] = [chunk.text for chunk in chunker.chunk(row["text"])]

        metadata = row.get("metadata", None)
        if prepend_metadata and metadata is not None:
            metadata = json.loads(metadata) if isinstance(metadata, str) else metadata
            row["chunks"] = [
                add_metadata(chunk, metadata, line_delimiter=".\n")
                for chunk in row["chunks"]
            ]
        tick()
        logger.info("chunker progress:  %d/%d", row_index + 1, total_rows)
        return row

    text_units = documents.apply(
        lambda row: chunker_with_logging(row, row.name), axis=1
    )

    text_units = cast("pd.DataFrame", text_units[["id", "chunks"]])
    text_units = text_units.explode("chunks")
    text_units.rename(
        columns={
            "id": "document_id",
            "chunks": "text",
        },
        inplace=True,
    )

    text_units["id"] = text_units.apply(
        lambda row: gen_sha512_hash(row, ["text"]), axis=1
    )
    # get a final token measurement
    text_units["n_tokens"] = text_units["text"].apply(
        lambda x: len(tokenizer.encode(x))
    )

    return cast(
        "pd.DataFrame", text_units[text_units["text"].notna()].reset_index(drop=True)
    )
