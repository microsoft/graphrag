# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Default method for loading config."""

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from string import Template
from typing import Any

import yaml
from dotenv import load_dotenv

from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.config.models.graph_rag_config import GraphRagConfig

_default_config_files = ["settings.yaml", "settings.yml", "settings.json"]


class _ConfigTextParser(ABC):
    """Abstract base class for parsing configuration text."""

    @abstractmethod
    def parse(self, text: str) -> dict[str, Any]:
        """Parse configuration text."""
        raise NotImplementedError


class _ConfigYamlParser(_ConfigTextParser):
    """Parse yaml configuration."""

    def parse(self, text: str) -> dict[str, Any]:
        """Parse yaml configuration text.

        Parameters
        ----------
        text : str
            The yaml configuration text.

        Returns
        -------
        dict[str, Any]
            The parsed configuration.
        """
        return yaml.safe_load(text)


class _ConfigJsonParser(_ConfigTextParser):
    """Parse json configuration."""

    def parse(self, text: str) -> dict[str, Any]:
        """Parse json configuration text.

        Parameters
        ----------
        text : str
            The json configuration text.

        Returns
        -------
        dict[str, Any]
            The parsed configuration.
        """
        return json.loads(text)


def _get_config_parser(file_extension: str) -> _ConfigTextParser:
    """Get the configuration parser based on the file extension.

    Parameters
    ----------
    file_extension : str
        The file extension.

    Returns
    -------
    ConfigTextParser
        The configuration parser.
    """
    match file_extension:
        case ".yaml" | ".yml":
            return _ConfigYamlParser()
        case ".json":
            return _ConfigJsonParser()
        case _:
            msg = (
                f"Unable to parse config. Unsupported file extension: {file_extension}"
            )
            raise ValueError(msg)


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


def load_config(
    root_dir: Path,
    config_filepath: Path | None = None,
) -> GraphRagConfig:
    """Load configuration from a file.

    Parameters
    ----------
    root_dir : str | Path
        The root directory of the project. Will search for the config file in this directory.
    config_filepath : str | None
        The path to the config file.
        If None, searches for config file in root.

    Returns
    -------
    GraphRagConfig
        The loaded configuration.
    """
    root = root_dir.resolve()
    config_path = _get_config_path(root, config_filepath)
    _load_dotenv(config_path)
    config_extension = config_path.suffix
    config_parser = _get_config_parser(config_extension)
    config_text = config_path.read_text(encoding="utf-8")
    config_text = _parse_env_variables(config_text)
    config_data = config_parser.parse(config_text)
    return create_graphrag_config(config_data, root_dir=str(root))
