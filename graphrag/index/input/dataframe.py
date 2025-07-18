# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing dataframe input loading method definition."""

import logging
from datetime import datetime
import pandas as pd

from graphrag.config.models.input_config import InputConfig
from graphrag.index.input.util import process_data_columns

log = logging.getLogger(__name__)


async def load_dataframe(
    config: InputConfig,
) -> pd.DataFrame:
    """Load input from a dataframe directly."""
    log.info("Loading data from input dataframe")
    dataframe = config.dataframe
    if dataframe is None:
        msg = "No input dataframe provided for dataframe input type"
        raise ValueError(msg)
    # Create a copy to avoid modifying the original dataframe
    data = dataframe.copy()
    
    # Process the data using the same logic as other loaders
    data = process_data_columns(data, config, "dataframe_input")
    # Set creation_date if not already present
    if "creation_date" not in data.columns:
        current_time = datetime.now().isoformat()
        data["creation_date"] = current_time
    
    return data
