# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""File management and utils for Incremental Indexing."""

from typing import NamedTuple

import pandas as pd

from graphrag.index.config.pipeline import PipelineConfig
from graphrag.index.storage.typing import PipelineStorage
from graphrag.utils.storage import _load_table_from_storage


# Output delta named tuple
class InputDelta(NamedTuple):
    """Named tuple for output delta."""

    new_inputs: pd.DataFrame
    deleted_inputs: pd.DataFrame


async def get_delta_docs(
    input_dataset: pd.DataFrame, storage: PipelineStorage
) -> InputDelta:
    final_docs = await _load_table_from_storage(
        "create_final_documents.parquet", storage
    )

    # Select distinct title from final docs and from dataset
    previous_docs = final_docs["title"].unique()
    dataset_docs = input_dataset["title"].unique()

    # Get the new documents
    new_docs = input_dataset[~input_dataset["title"].isin(previous_docs)]
    deleted_docs = final_docs[~final_docs["title"].isin(dataset_docs)]
    return InputDelta(new_docs, deleted_docs)
