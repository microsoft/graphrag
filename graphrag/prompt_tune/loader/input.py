# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Input loading module."""

from typing import cast

import pandas as pd
from datashaper import NoopVerbCallbacks, TableContainer, VerbInput

from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.input import load_input
from graphrag.index.progress.types import ProgressReporter
from graphrag.index.verbs import chunk

MIN_CHUNK_SIZE = 200
MIN_CHUNK_OVERLAP = 0


async def load_docs_in_chunks(
    root: str,
    config: GraphRagConfig,
    select_method: str,
    limit: int,
    reporter: ProgressReporter,
    chunk_size: int = MIN_CHUNK_SIZE,
) -> list[str]:
    """Load docs into chunks for generating prompts."""
    dataset = await load_input(config.input, reporter, root)

    # covert to text units
    input = VerbInput(input=TableContainer(table=dataset))
    chunk_strategy = config.chunks.resolved_strategy()

    # Use smaller chunks, to avoid huge prompts
    chunk_strategy["chunk_size"] = chunk_size
    chunk_strategy["chunk_overlap"] = MIN_CHUNK_OVERLAP

    dataset_chunks_table_container = chunk(
        input,
        column="text",
        to="chunks",
        callbacks=NoopVerbCallbacks(),
        strategy=chunk_strategy,
    )

    dataset_chunks = cast(pd.DataFrame, dataset_chunks_table_container.table)

    # Select chunks into a new df and explode it
    chunks_df = pd.DataFrame(dataset_chunks["chunks"].explode())  # type: ignore

    # Depending on the select method, build the dataset
    if limit <= 0 or limit > len(chunks_df):
        limit = len(chunks_df)

    if select_method == "top":
        chunks_df = chunks_df[:limit]
    elif select_method == "random":
        chunks_df = chunks_df.sample(n=limit)

    # Convert the dataset to list form, so we have a list of documents
    return chunks_df["chunks"].tolist()
