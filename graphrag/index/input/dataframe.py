# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing dataframe input loading method definition."""

import logging
from datetime import datetime
from typing import Any

import pandas as pd

from graphrag.config.models.input_config import InputConfig
from graphrag.index.input.util import process_data_columns
from graphrag.index.utils.hashing import gen_sha512_hash

log = logging.getLogger(__name__)


async def load_dataframe(
    config: InputConfig,
    dataframe: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Load input from a dataframe directly."""
    log.info("Loading data from input dataframe")
    
    # If no dataframe provided directly, try to get it from the global registry
    if dataframe is None:
        from graphrag.api.dataframe_input import get_current_dataframe
        dataframe = get_current_dataframe()
    
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
    
    # Ensure required columns exist
    if "id" not in data.columns:
        data["id"] = data.apply(
            lambda x: gen_sha512_hash(x, x.keys()), axis=1
        )
    
    if "text" not in data.columns and config.text_column is not None:
        if config.text_column in data.columns:
            data["text"] = data[config.text_column]
        else:
            msg = f"text_column '{config.text_column}' not found in input dataframe"
            raise ValueError(msg)
    elif "text" not in data.columns:
        msg = "No 'text' column found in input dataframe and no text_column configured"
        raise ValueError(msg)
    
    if "title" not in data.columns:
        if config.title_column is not None and config.title_column in data.columns:
            data["title"] = data[config.title_column]
        else:
            # Generate default titles based on row index
            data["title"] = data.apply(lambda x: f"document_{x.name}", axis=1)
    
    log.info("Loaded %d rows from input dataframe", len(data))
    
    return data 