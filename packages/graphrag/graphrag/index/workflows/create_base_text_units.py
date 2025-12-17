# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import json
import logging
from typing import Any, cast

import pandas as pd

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.chunking.chunker import Chunker, create_chunker
from graphrag.config.models.chunking_config import ChunkingConfig
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.index.utils.hashing import gen_sha512_hash
from graphrag.logger.progress import progress_ticker
from graphrag.tokenizer.get_tokenizer import get_tokenizer
from graphrag.utils.storage import load_table_from_storage, write_table_to_storage

logger = logging.getLogger(__name__)


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """All the steps to transform base text_units."""
    logger.info("Workflow started: create_base_text_units")
    documents = await load_table_from_storage("documents", context.output_storage)

    output = create_base_text_units(documents, context.callbacks, config.chunks)

    await write_table_to_storage(output, "text_units", context.output_storage)

    logger.info("Workflow completed: create_base_text_units")
    return WorkflowFunctionOutput(result=output)


def create_base_text_units(
    documents: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    chunks_config: ChunkingConfig,
) -> pd.DataFrame:
    """All the steps to transform base text_units."""
    documents.sort_values(by=["id"], ascending=[True], inplace=True)

    size = chunks_config.size
    encoding_model = chunks_config.encoding_model
    prepend_metadata = chunks_config.prepend_metadata
    chunk_size_includes_metadata = chunks_config.chunk_size_includes_metadata

    tokenizer = get_tokenizer(encoding_model=encoding_model)
    num_total = _get_num_total(documents, "text")
    tick = progress_ticker(callbacks.progress, num_total)

    def chunker_fn(row: pd.Series) -> Any:
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
                metadata_tokens = len(tokenizer.encode(metadata_str))
                if metadata_tokens >= size:
                    message = "Metadata tokens exceeds the maximum tokens per chunk. Please increase the tokens per chunk."
                    raise ValueError(message)

        chunks_config.size = size - metadata_tokens
        chunker = create_chunker(chunks_config)

        chunked = _chunk_text(
            pd.DataFrame([row]).reset_index(drop=True),
            column="text",
            chunker=chunker,
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
        tick()
        return row

    # Track progress of row-wise apply operation
    total_rows = len(documents)
    logger.info("Starting chunking process for %d documents", total_rows)

    def chunker_with_logging(row: pd.Series, row_index: int) -> Any:
        """Add logging to chunker execution."""
        result = chunker_fn(row)
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
    text_units["n_tokens"] = text_units["text"].apply(
        lambda x: len(tokenizer.encode(x))
    )

    return cast(
        "pd.DataFrame", text_units[text_units["text"].notna()].reset_index(drop=True)
    )


def _get_num_total(output: pd.DataFrame, column: str) -> int:
    num_total = 0
    for row in output[column]:
        if isinstance(row, str):
            num_total += 1
        else:
            num_total += len(row)
    return num_total


def _chunk_text(
    input: pd.DataFrame,
    column: str,
    chunker: Chunker,
) -> pd.Series:
    return cast(
        "pd.Series",
        input.apply(
            cast(
                "Any",
                lambda x: chunker.chunk(x[column]),
            ),
            axis=1,
        ),
    )
