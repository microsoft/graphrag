# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging
from typing import Any

import pandas as pd
from graphrag_chunking.chunker import Chunker
from graphrag_chunking.chunker_factory import create_chunker
from graphrag_chunking.transformers import add_metadata
from graphrag_input import TextDocument
from graphrag_llm.tokenizer import Tokenizer
from graphrag_storage.tables.table import Table

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.index.utils.hashing import gen_sha512_hash
from graphrag.logger.progress import progress_ticker
from graphrag.tokenizer.get_tokenizer import get_tokenizer

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """All the steps to transform base text_units."""
    logger.info("Workflow started: create_base_text_units")

    tokenizer = get_tokenizer(encoding_model=config.chunking.encoding_model)
    chunker = create_chunker(config.chunking, tokenizer.encode, tokenizer.decode)

    async with context.output_table_provider.open("documents") as documents_table:
        total_rows = await documents_table.length()
        output = await create_base_text_units(
            documents_table,
            total_rows,
            context.callbacks,
            tokenizer=tokenizer,
            chunker=chunker,
            prepend_metadata=config.chunking.prepend_metadata,
        )

    await context.output_table_provider.write_dataframe("text_units", output)

    logger.info("Workflow completed: create_base_text_units")
    return WorkflowFunctionOutput(result=output)


async def create_base_text_units(
    documents_table: Table,
    total_rows: int,
    callbacks: WorkflowCallbacks,
    tokenizer: Tokenizer,
    chunker: Chunker,
    prepend_metadata: list[str] | None = None,
) -> pd.DataFrame:
    """Transform documents into chunked text units via streaming read.

    Reads documents row-by-row from an async iterable to avoid loading the
    entire documents table into memory at once. Chunks each document
    individually and collects the resulting text units into a DataFrame.

    Args
    ----
        documents_table: Table
            Table instance representing the documents. Supports async iteration over document rows.
        total_rows: int
            Total number of documents for progress reporting.
        callbacks: WorkflowCallbacks
            Callbacks for progress reporting.
        tokenizer: Tokenizer
            Tokenizer for measuring chunk token counts.
        chunker: Chunker
            Chunker instance for splitting document text.
        prepend_metadata: list[str] | None
            Optional list of metadata fields to prepend to
            each chunk.

    Returns
    -------
        pd.DataFrame:
            DataFrame with columns: id, document_id, text,
            n_tokens.
    """
    tick = progress_ticker(callbacks.progress, total_rows)

    logger.info(
        "Starting chunking process for %d documents",
        total_rows,
    )

    rows: list[dict[str, Any]] = []
    doc_index = 0

    async for doc in documents_table:
        chunks = chunk_document(doc, chunker, prepend_metadata)
        for chunk_text in chunks:
            if chunk_text is None:
                continue
            row = {
                "document_id": doc["id"],
                "text": chunk_text,
            }
            row["id"] = gen_sha512_hash(row, ["text"])
            row["n_tokens"] = len(tokenizer.encode(chunk_text))
            rows.append(row)

        doc_index += 1
        tick()
        logger.info(
            "chunker progress:  %d/%d",
            doc_index,
            total_rows,
        )
        # //write

    df = pd.DataFrame(rows, columns=["id", "document_id", "text", "n_tokens"])
    return df.sort_values(by=["document_id", "id"]).reset_index(drop=True)


def chunk_document(
    doc: dict[str, Any],
    chunker: Chunker,
    prepend_metadata: list[str] | None = None,
) -> list[str]:
    """Chunk a single document row into text fragments.

    Args
    ----
        doc: dict[str, Any]
            A single document row as a dictionary.
        chunker: Chunker
            Chunker instance for splitting text.
        prepend_metadata: list[str] | None
            Optional metadata fields to prepend.

    Returns
    -------
        list[str]:
            List of chunk text strings.
    """
    transformer = None
    if prepend_metadata:
        document = TextDocument(
            id=doc["id"],
            title=doc.get("title", ""),
            text=doc["text"],
            creation_date=doc.get("creation_date", ""),
            raw_data=doc.get("raw_data"),
        )
        metadata = document.collect(prepend_metadata)
        transformer = add_metadata(metadata=metadata, line_delimiter=".\n")

    return [chunk.text for chunk in chunker.chunk(doc["text"], transform=transformer)]
