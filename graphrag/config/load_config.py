# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Default method for loading config."""

from pathlib import Path

from .config_file_loader import load_config_from_file, search_for_config_in_root_dir
from .create_graphrag_config import create_graphrag_config
from .models.graph_rag_config import GraphRagConfig


def load_config(
    root_dir: str | Path,
    config_filepath: str | None = None,
) -> GraphRagConfig:
    """Load configuration from a file or create a default configuration.

    If a config file is not found the default configuration is created.

    Parameters
    ----------
    root_dir : str | Path
        The root directory of the project. Will search for the config file in this directory.
    config_filepath : str | None
        The path to the config file.
        If None, searches for config file in root and
        if not found creates a default configuration.
    """
    root = Path(root_dir).resolve()

    # If user specified a config file path then it is required
    if config_filepath:
        config_path = Path(config_filepath).resolve()
        if not config_path.exists():
            msg = f"Specified Config file not found: {config_path}"
            raise FileNotFoundError(msg)
    else:
        # resolve config filepath from the root directory if it exists
        config_path = search_for_config_in_root_dir(root)
    if config_path:
        config = load_config_from_file(config_path)
    else:
        config = create_graphrag_config(root_dir=str(root))

    return config
