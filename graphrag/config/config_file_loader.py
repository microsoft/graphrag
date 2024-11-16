# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Load a GraphRagConfiguration from a file."""

import json
from abc import ABC, abstractmethod
from pathlib import Path

import yaml

from graphrag.config.create_graphrag_config import create_graphrag_config
from graphrag.config.models.graph_rag_config import GraphRagConfig

_default_config_files = ["settings.yaml", "settings.yml", "settings.json"]


def search_for_config_in_root_dir(root: str | Path) -> Path | None:
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


class ConfigFileLoader(ABC):
    """Base class for loading a configuration from a file."""

    @abstractmethod
    def load_config(self, config_path: str | Path) -> GraphRagConfig:
        """Load configuration from a file."""
        raise NotImplementedError


class ConfigYamlLoader(ConfigFileLoader):
    """Load a configuration from a yaml file."""

    def load_config(self, config_path: str | Path) -> GraphRagConfig:
        """Load a configuration from a yaml file.

        Parameters
        ----------
        config_path : str | Path
            The path to the yaml file to load.

        Returns
        -------
        GraphRagConfig
            The loaded configuration.

        Raises
        ------
        ValueError
            If the file extension is not .yaml or .yml.
        FileNotFoundError
            If the config file is not found.
        """
        config_path = Path(config_path)
        if config_path.suffix not in [".yaml", ".yml"]:
            msg = f"Invalid file extension for loading yaml config from: {config_path!s}. Expected .yaml or .yml"
            raise ValueError(msg)
        root_dir = str(config_path.parent)
        if not config_path.is_file():
            msg = f"Config file not found: {config_path}"
            raise FileNotFoundError(msg)
        with config_path.open("rb") as file:
            data = yaml.safe_load(file.read().decode(encoding="utf-8", errors="strict"))
            return create_graphrag_config(data, root_dir)


class ConfigJsonLoader(ConfigFileLoader):
    """Load a configuration from a json file."""

    def load_config(self, config_path: str | Path) -> GraphRagConfig:
        """Load a configuration from a json file.

        Parameters
        ----------
        config_path : str | Path
            The path to the json file to load.

        Returns
        -------
        GraphRagConfig
            The loaded configuration.

        Raises
        ------
        ValueError
            If the file extension is not .json.
        FileNotFoundError
            If the config file is not found.
        """
        config_path = Path(config_path)
        root_dir = str(config_path.parent)
        if config_path.suffix != ".json":
            msg = f"Invalid file extension for loading json config from: {config_path!s}. Expected .json"
            raise ValueError(msg)
        if not config_path.is_file():
            msg = f"Config file not found: {config_path}"
            raise FileNotFoundError(msg)
        with config_path.open("rb") as file:
            data = json.loads(file.read().decode(encoding="utf-8", errors="strict"))
            return create_graphrag_config(data, root_dir)


def get_config_file_loader(config_path: str | Path) -> ConfigFileLoader:
    """Config File Loader Factory.

    Parameters
    ----------
    config_path : str | Path
        The path to the config file.

    Returns
    -------
    ConfigFileLoader
        The config file loader for the provided config file.

    Raises
    ------
    ValueError
        If the config file extension is not supported.
    """
    config_path = Path(config_path)
    ext = config_path.suffix
    match ext:
        case ".yaml" | ".yml":
            return ConfigYamlLoader()
        case ".json":
            return ConfigJsonLoader()
        case _:
            msg = f"Unsupported config file extension: {ext}"
            raise ValueError(msg)


def load_config_from_file(config_path: str | Path) -> GraphRagConfig:
    """Load a configuration from a file.

    Parameters
    ----------
    config_path : str | Path
        The path to the configuration file.
        Supports .yaml, .yml, and .json config files.

    Returns
    -------
    GraphRagConfig
        The loaded configuration.

    Raises
    ------
    ValueError
        If the file extension is not supported.
    FileNotFoundError
        If the config file is not found.
    """
    loader = get_config_file_loader(config_path)
    return loader.load_config(config_path)
