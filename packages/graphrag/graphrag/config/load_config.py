# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Default method for loading config."""

from pathlib import Path
from typing import Any

import graphrag_common.config as graphrag_config

from graphrag.config.models.graph_rag_config import GraphRagConfig

_default_config_files = ["settings.yaml", "settings.yml", "settings.json"]


def _search_for_config_in_root_dir(root: str | Path) -> Path | None:
    """Resolve the config path from the given root directory.

    Parameters
    ----------
    root : str | Path
        The path to the root directory containing the config file.
        Searches for a default config file (settings.{yaml,yml,json}).

    Returns
    -------
    Path | None
        returns a Path if there is a config in the root directory
        Otherwise returns None.
    """
    root = Path(root)

    if not root.is_dir():
        msg = f"Invalid config path: {root} is not a directory"
        raise FileNotFoundError(msg)

    for file in _default_config_files:
        if (root / file).is_file():
            return root / file

    return None


def _get_config_path(root_dir: Path, config_filepath: Path | None) -> Path:
    """Get the configuration file path.

    Parameters
    ----------
    root_dir : str | Path
        The root directory of the project. Will search for the config file in this directory.
    config_filepath : str | None
        The path to the config file.
        If None, searches for config file in root.

    Returns
    -------
    Path
        The configuration file path.
    """
    if config_filepath:
        config_path = config_filepath.resolve()
        if not config_path.exists():
            msg = f"Specified Config file not found: {config_path}"
            raise FileNotFoundError(msg)
    else:
        config_path = _search_for_config_in_root_dir(root_dir)

    if not config_path:
        msg = f"Config file not found in root directory: {root_dir}"
        raise FileNotFoundError(msg)

    return config_path


def load_config(
    root_dir: Path,
    config_filepath: Path | None = None,
    cli_overrides: dict[str, Any] | None = None,
) -> GraphRagConfig:
    """Load configuration from a file.

    Parameters
    ----------
    root_dir : str | Path
        The root directory of the project. Will search for the config file in this directory.
    config_filepath : str | None
        The path to the config file.
        If None, searches for config file in root.
    cli_overrides : dict[str, Any] | None
        A flat dictionary of cli overrides.
        Example: {'output.base_dir': 'override_value'}

    Returns
    -------
    GraphRagConfig
        The loaded configuration.

    Raises
    ------
    FileNotFoundError
        If the config file is not found.
    ConfigParsingError
        If there was an error parsing the config file or its environment variables.
    ValidationError
        If there are pydantic validation errors when instantiating the config.
    """
    config_path = _get_config_path(root_dir, config_filepath)
    dotenv_path = config_path.parent / ".env"
    dotenv_path = dotenv_path if dotenv_path.is_file() else None
    return graphrag_config.load_config(
        config_initializer=GraphRagConfig,
        config_path=config_path,
        overrides=cli_overrides,
        dot_env_path=dotenv_path,
    )
