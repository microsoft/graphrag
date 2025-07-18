# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""High-level API for using dataframes as input to GraphRAG."""

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from graphrag.api.index import build_index
from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.config.enums import IndexingMethod, InputFileType
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.logger.base import ProgressLogger

log = logging.getLogger(__name__)


async def index_dataframe(
    input_dataframe: pd.DataFrame,
    output_dir: str | Path,
    config_path: str | Path | None = None,
    config_data: dict[str, Any] | None = None,
    text_column: str = "text",
    title_column: str | None = "title", 
    metadata_columns: list[str] | None = None,
    method: IndexingMethod | str = IndexingMethod.Standard,
    progress_logger: ProgressLogger | None = None,
) -> None:
    """Index a dataframe using GraphRAG.
    
    Args:
        input_dataframe: The pandas DataFrame containing the documents to index
        output_dir: Directory where the indexing outputs will be saved
        config_path: Path to GraphRAG configuration file (optional)
        config_data: Configuration data as a dictionary (optional, alternative to config_path)
        text_column: Name of the column containing the document text (default: "text")
        title_column: Name of the column containing document titles (default: "title")
        metadata_columns: List of column names to include as metadata (optional)
        method: The indexing method to use (default: IndexingMethod.Standard)
        progress_logger: Progress logger instance (optional)
    
    Returns:
        None
        
    Raises:
        ValueError: If required columns are missing or configuration is invalid
    """
    # Validate input dataframe
    if input_dataframe.empty:
        msg = "Input dataframe is empty"
        raise ValueError(msg)
    
    if text_column not in input_dataframe.columns:
        msg = f"Text column '{text_column}' not found in input dataframe"
        raise ValueError(msg)
    
    # Set up configuration
    if config_data is None:
        config_data = {}
    
    # Configure input settings for dataframe
    config_data.setdefault("input", {})
    config_data["input"]["file_type"] = InputFileType.dataframe.value
    config_data["input"]["text_column"] = text_column
    if title_column is not None:
        config_data["input"]["title_column"] = title_column
    if metadata_columns is not None:
        config_data["input"]["metadata"] = metadata_columns
    
    # Configure output directory
    config_data.setdefault("output", {})
    config_data["output"]["base_dir"] = str(output_dir)
    
    # Create GraphRAG configuration
    if config_path is not None:
        from graphrag.config.load_config import load_config
        config = load_config(Path.cwd(), Path(config_path))
        # Apply our dataframe-specific overrides
        config.input.file_type = InputFileType.dataframe
        config.input.text_column = text_column
        if title_column is not None:
            config.input.title_column = title_column
        if metadata_columns is not None:
            config.input.metadata = metadata_columns
        config.output.base_dir = str(output_dir)
    else:
        # Create from scratch with our data
        config = create_graphrag_config(config_data, str(Path.cwd()))

    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    log.info(f"Starting GraphRAG indexing from dataframe with {len(input_dataframe)} documents")
    
    # Store the dataframe in a global registry so the dataframe loader can access it
    global _current_input_dataframe
    _current_input_dataframe = input_dataframe
    
    try:
        # Run the indexing pipeline
        results = await build_index(
            config=config,
            method=method,
            progress_logger=progress_logger,
        )
        
        log.info(f"GraphRAG indexing completed. Outputs saved to {output_dir}")
        
        # Check for any errors in the pipeline results
        for result in results:
            if result.errors:
                log.error(f"Errors in workflow {result.workflow}: {result.errors}")
    
    finally:
        # Clean up the global dataframe reference
        _current_input_dataframe = None


# Global variable to store the current dataframe being processed
_current_input_dataframe: pd.DataFrame | None = None


def get_current_input_dataframe() -> pd.DataFrame | None:
    """Get the currently registered input dataframe.
    
    Returns:
        The current input dataframe if one is registered, None otherwise
    """
    return _current_input_dataframe