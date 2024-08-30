# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Default method for loading config."""

from pathlib import Path

from .config_file_loader import load_config_from_file, resolve_config_path_with_root
from .create_graphrag_config import create_graphrag_config
from .models.graph_rag_config import GraphRagConfig
from .resolve_timestamp_path import resolve_timestamp_path


def load_config(
    root_dir: str | Path,
    config_filepath: str | Path | None = None,
    run_id: str | None = None,
) -> GraphRagConfig:
    """Load configuration from a file or create a default configuration.

    If a config file is not found the default configuration is created.

    Parameters
    ----------
    root_dir : str | Path
        The root directory of the project. Will search for the config file in this directory.
    config_filepath : str | Path | None
        The path to the config file.
        If None, searches for config file in root and
        if not found creates a default configuration.
    run_id : str | None
        The run id to use for resolving timestamp_paths.
    """
    root = Path(root_dir).resolve()

    # If user specified a config file path then it is required
    if config_filepath is not None:
        config_path = (root / config_filepath).resolve()
        if not config_path.exists():
            msg = f"Specified Config file not found: {config_path}"
            raise FileNotFoundError(msg)

    # Else optional resolve the config path from the root directory if it exists
    try:
        config_path = resolve_config_path_with_root(root)
        config = load_config_from_file(config_path)
    except FileNotFoundError:
        # If config file not found in root directory create default configuration
        config = create_graphrag_config(root_dir=str(root))

    if run_id is not None:
        config.storage.base_dir = str(
            resolve_timestamp_path((root / config.storage.base_dir).resolve(), run_id)
        )
        config.reporting.base_dir = str(
            resolve_timestamp_path((root / config.reporting.base_dir).resolve(), run_id)
        )
    else:
        config.storage.base_dir = str((root / config.storage.base_dir).resolve())
        config.reporting.base_dir = str((root / config.reporting.base_dir).resolve())

    return config
