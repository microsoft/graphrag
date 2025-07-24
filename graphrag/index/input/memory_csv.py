# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing load method definition."""

import logging
from datetime import datetime
from datetime import timezone as datetime_tz

import pandas as pd

from graphrag.config.models.input_config import InputConfig
from graphrag.index.input.util import load_files_from_memory, process_data_columns

logger = logging.getLogger(__name__)


def load_memory_csv(
    config: InputConfig,
    input_files: list[pd.DataFrame],
) -> pd.DataFrame:
    """Load csv inputs from a directory."""
    logger.info("Loading csv files from %s", config.storage.base_dir)

    if input_files is not None and len(input_files) == 0:
        error_msg = "input_files is an empty list, no files to load."
        raise ValueError(error_msg)

    def load_file(
        group: dict | None, input_file: pd.DataFrame = pd.DataFrame()
    ) -> pd.DataFrame:
        if group is None:
            group = {}

        data = input_file

        additional_keys = group.keys()
        if len(additional_keys) > 0:
            data[[*additional_keys]] = data.apply(
                lambda _row: pd.Series([group[key] for key in additional_keys]), axis=1
            )

        data = process_data_columns(data, config, "No path needed for in memory CSV")

        creation_date = datetime.now(datetime_tz.utc).strftime("%Y-%m-%d %H:%M:%S")

        data["creation_date"] = data.apply(lambda _: creation_date, axis=1)

        return data

    return load_files_from_memory(load_file, config, input_files=input_files)
