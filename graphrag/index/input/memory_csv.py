# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing load method definition."""

import logging
from io import BytesIO

import pandas as pd

from datetime import datetime
from graphrag.config.models.input_config import InputConfig
from graphrag.index.input.util import load_files_from_memory, process_data_columns
from graphrag.storage.pipeline_storage import PipelineStorage

logger = logging.getLogger(__name__)

async def load_memory_csv(
    config: InputConfig,
    storage: PipelineStorage,
    input_files: list[pd.DataFrame],
) -> pd.DataFrame:
    """Load csv inputs from a directory."""
    logger.info("Loading csv files from %s", config.storage.base_dir)

    if input_files is not None and len(input_files) == 0:
        raise ValueError("input_files should be a list of DataFrames, not a single DataFrame.")

    async def load_file(path: str | None, group: dict | None, input_file: pd.DataFrame = pd.DataFrame()) -> pd.DataFrame:
        if group is None:
            group = {}

        data = input_file

        additional_keys = group.keys()
        if len(additional_keys) > 0:
            data[[*additional_keys]] = data.apply(
                lambda _row: pd.Series([group[key] for key in additional_keys]), axis=1
            )

        data = process_data_columns(data, config, "No path needed for in memory CSV")
        
        creation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
        data["creation_date"] = data.apply(lambda _: creation_date, axis=1)

        return data

    return await load_files_from_memory(load_file, config, storage, input_files=input_files)
