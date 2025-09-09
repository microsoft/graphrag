# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import json
import logging
from typing import Any, cast

import pandas as pd

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.chunking_config import ChunkStrategyType
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.operations.chunk_text.chunk_text import chunk_text
from graphrag.index.operations.chunk_text.strategies import get_encoding_fn
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.index.utils.hashing import gen_sha512_hash
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """All the steps to transform base text_units."""
    logger.info("Workflow started: create_base_text_units")
    documents = await load_table_from_storage("documents", context.output_storage)

    chunks = config.chunks

    output = create_base_text_units(
        documents,
        context.callbacks,
        chunks.size,
        chunks.overlap,
        chunks.encoding_model,
        strategy=chunks.strategy,
        prepend_metadata=chunks.prepend_metadata,
        chunk_size_includes_metadata=chunks.chunk_size_includes_metadata,
    )

    await write_table_to_storage(output, "text_units", context.output_storage)

    logger.info("Workflow completed: create_base_text_units")
    return WorkflowFunctionOutput(result=output)


def create_base_text_units(
    documents: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    size: int,
    overlap: int,
    encoding_model: str,
    strategy: ChunkStrategyType,
    prepend_metadata: bool = False,
    chunk_size_includes_metadata: bool = False,
) -> pd.DataFrame:
    """All the steps to transform base text_units."""
    documents.sort_values(by=["id"], ascending=[True], inplace=True)

    encode, _ = get_encoding_fn(encoding_model)

    def chunker(row: pd.Series) -> Any:
        line_delimiter = ".\n"
        metadata_str = ""
        metadata_tokens = 0

        if prepend_metadata and "metadata" in row:
            metadata = row["metadata"]
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            if isinstance(metadata, dict):
                metadata_str = (
                    line_delimiter.join(f"{k}: {v}" for k, v in metadata.items())
                    + line_delimiter
                )

            if chunk_size_includes_metadata:
                metadata_tokens = len(encode(metadata_str))
                if metadata_tokens >= size:
                    message = "Metadata tokens exceeds the maximum tokens per chunk. Please increase the tokens per chunk."
                    raise ValueError(message)

        chunked = chunk_text(
            pd.DataFrame([row]).reset_index(drop=True),
            column="text",
            size=size - metadata_tokens,
            overlap=overlap,
            encoding_model=encoding_model,
            strategy=strategy,
            callbacks=callbacks,
        )[0]

        if prepend_metadata:
            for index, chunk in enumerate(chunked):
                if isinstance(chunk, str):
                    chunked[index] = metadata_str + chunk
                else:
                    chunked[index] = (
                        (chunk[0], metadata_str + chunk[1], chunk[2]) if chunk else None
                    )

        row["chunks"] = chunked
        return row

    # Track progress of row-wise apply operation
    total_rows = len(documents)
    logger.info("Starting chunking process for %d documents", total_rows)

    def chunker_with_logging(row: pd.Series, row_index: int) -> Any:
        """Add logging to chunker execution."""
        result = chunker(row)
        logger.info("chunker progress:  %d/%d", row_index + 1, total_rows)
        return result

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
    text_units["n_tokens"] = text_units["text"].apply(lambda x: len(encode(x)))

    return cast(
        "pd.DataFrame", text_units[text_units["text"].notna()].reset_index(drop=True)
    )
