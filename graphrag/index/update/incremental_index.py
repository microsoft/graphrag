# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Dataframe operations and utils for Incremental Indexing."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from graphrag.storage.pipeline_storage import PipelineStorage
from graphrag.utils.storage import (
    load_table_from_storage,
    write_table_to_storage,
)


@dataclass
class InputDelta:
    """Dataclass to hold the input delta.

    Attributes
    ----------
    new_inputs : pd.DataFrame
        The new inputs.
    deleted_inputs : pd.DataFrame
        The deleted inputs.
    """

    new_inputs: pd.DataFrame
    deleted_inputs: pd.DataFrame


async def get_delta_docs(
    input_dataset: pd.DataFrame, storage: PipelineStorage
) -> InputDelta:
    """Get the delta between the input dataset and the final documents.

    Parameters
    ----------
    input_dataset : pd.DataFrame
        The input dataset.
    storage : PipelineStorage
        The Pipeline storage.

    Returns
    -------
    InputDelta
        The input delta. With new inputs and deleted inputs.
    """
    final_docs = await load_table_from_storage("documents", storage)

    # Select distinct title from final docs and from dataset
    previous_docs: list[str] = final_docs["title"].unique().tolist()
    dataset_docs: list[str] = input_dataset["title"].unique().tolist()

    # Get the new documents (using loc to ensure DataFrame)
    new_docs = input_dataset.loc[~input_dataset["title"].isin(previous_docs)]

    # Get the deleted documents (again using loc to ensure DataFrame)
    deleted_docs = final_docs.loc[~final_docs["title"].isin(dataset_docs)]

    return InputDelta(new_docs, deleted_docs)


async def concat_dataframes(
    name: str,
    previous_storage: PipelineStorage,
    delta_storage: PipelineStorage,
    output_storage: PipelineStorage,
) -> pd.DataFrame:
    """Concatenate dataframes."""
    old_df = await load_table_from_storage(name, previous_storage)
    delta_df = await load_table_from_storage(name, delta_storage)

    # Merge the final documents
    initial_id = old_df["human_readable_id"].max() + 1
    delta_df["human_readable_id"] = np.arange(initial_id, initial_id + len(delta_df))
    final_df = pd.concat([old_df, delta_df], ignore_index=True, copy=False)

    await write_table_to_storage(final_df, name, output_storage)

    return final_df
