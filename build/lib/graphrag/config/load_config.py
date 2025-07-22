# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Default method for loading config."""

import json
import os
from pathlib import Path
from string import Template
from typing import Any

import yaml
from dotenv import load_dotenv

from graphrag.config.create_graphrag_config import create_graphrag_config
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


def _parse_env_variables(text: str) -> str:
    """Parse environment variables in the configuration text.

    Parameters
    ----------
    text : str
        The configuration text.

    Returns
    -------
    str
        The configuration text with environment variables parsed.

    Raises
    ------
    KeyError
        If an environment variable is not found.
    """
    return Template(text).substitute(os.environ)


def _load_dotenv(config_path: Path | str) -> None:
    """Load the .env file if it exists in the same directory as the config file.

    Parameters
    ----------
    config_path : Path | str
        The path to the config file.
    """
    config_path = Path(config_path)
    dotenv_path = config_path.parent / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path)


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


def _apply_overrides(data: dict[str, Any], overrides: dict[str, Any]) -> None:
    """Apply the overrides to the raw configuration."""
    for key, value in overrides.items():
        keys = key.split(".")
        target = data
        current_path = keys[0]
        for k in keys[:-1]:
            current_path += f".{k}"
            target_obj = target.get(k, {})
            if not isinstance(target_obj, dict):
                msg = f"Cannot override non-dict value: data[{current_path}] is not a dict."
                raise TypeError(msg)
            target[k] = target_obj
            target = target[k]
        target[keys[-1]] = value


def _parse(file_extension: str, contents: str) -> dict[str, Any]:
    """Parse configuration."""
    match file_extension:
        case ".yaml" | ".yml":
            return yaml.safe_load(contents)
        case ".json":
            return json.loads(contents)
        case _:
            msg = (
                f"Unable to parse config. Unsupported file extension: {file_extension}"
            )
            raise ValueError(msg)


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
    ValueError
        If the config file extension is not supported.
    TypeError
        If applying cli overrides to the config fails.
    KeyError
        If config file references a non-existent environment variable.
    ValidationError
        If there are pydantic validation errors when instantiating the config.
    """
    root = root_dir.resolve()
    config_path = _get_config_path(root, config_filepath)
    _load_dotenv(config_path)
    config_extension = config_path.suffix
    config_text = config_path.read_text(encoding="utf-8")
    config_text = _parse_env_variables(config_text)
    config_data = _parse(config_extension, config_text)
    if cli_overrides:
        _apply_overrides(config_data, cli_overrides)
    return create_graphrag_config(config_data, root_dir=str(root))
