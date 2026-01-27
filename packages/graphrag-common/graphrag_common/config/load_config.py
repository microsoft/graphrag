# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Load configuration."""

import json
import os
from collections.abc import Callable
from pathlib import Path
from string import Template
from typing import Any, TypeVar

import yaml
from dotenv import load_dotenv

T = TypeVar("T", covariant=True)

_default_config_files = ["settings.yaml", "settings.yml", "settings.json"]


class ConfigParsingError(ValueError):
    """Configuration Parsing Error."""

    def __init__(self, msg: str) -> None:
        """Initialize the ConfigParsingError."""
        super().__init__(msg)


def _get_config_file_path(config_dir_or_file: Path) -> Path:
    """Resolve the config path from the given directory or file."""
    config_dir_or_file = Path(config_dir_or_file)

    if config_dir_or_file.is_file():
        return config_dir_or_file

    if not config_dir_or_file.is_dir():
        msg = f"Invalid config path: {config_dir_or_file} is not a directory"
        raise FileNotFoundError(msg)

    for file in _default_config_files:
        if (config_dir_or_file / file).is_file():
            return config_dir_or_file / file

    msg = f"No 'settings.[yaml|yml|json]' config file found in directory: {config_dir_or_file}"
    raise FileNotFoundError(msg)


def _load_dotenv(env_file_path: Path, required: bool) -> None:
    """Load the .env file if it exists."""
    if not env_file_path.is_file():
        if not required:
            return
        msg = f"dot_env_path not found: {env_file_path}"
        raise FileNotFoundError(msg)
    load_dotenv(env_file_path)


def _parse_json(data: str) -> dict[str, Any]:
    """Parse JSON data."""
    return json.loads(data)


def _parse_yaml(data: str) -> dict[str, Any]:
    """Parse YAML data."""
    return yaml.safe_load(data)


def _get_parser_for_file(file_path: str | Path) -> Callable[[str], dict[str, Any]]:
    """Get the parser for the given file path."""
    file_path = Path(file_path).resolve()
    match file_path.suffix.lower():
        case ".json":
            return _parse_json
        case ".yaml" | ".yml":
            return _parse_yaml
        case _:
            msg = (
                f"Failed to parse, {file_path}. Unsupported file extension, "
                + f"{file_path.suffix}. Pass in a custom config_parser argument or "
                + "use one of the supported file extensions, .json, .yaml, .yml, .toml."
            )
            raise ConfigParsingError(msg)


def _parse_env_variables(text: str) -> str:
    """Parse environment variables in the configuration text."""
    try:
        return Template(text).substitute(os.environ)
    except KeyError as error:
        msg = f"Environment variable not found: {error}"
        raise ConfigParsingError(msg) from error


def _recursive_merge_dicts(dest: dict[str, Any], src: dict[str, Any]) -> None:
    """Recursively merge two dictionaries in place."""
    for key, value in src.items():
        if isinstance(value, dict):
            if isinstance(dest.get(key), dict):
                _recursive_merge_dicts(dest[key], value)
            else:
                dest[key] = value
        else:
            dest[key] = value


def load_config(
    config_initializer: Callable[..., T],
    config_path: str | Path | None = None,
    overrides: dict[str, Any] | None = None,
    set_cwd: bool = True,
    parse_env_vars: bool = True,
    load_dot_env_file: bool = True,
    dot_env_path: str | Path | None = None,
    config_parser: Callable[[str], dict[str, Any]] | None = None,
    file_encoding: str = "utf-8",
) -> T:
    """Load configuration from a file.

    Parameters
    ----------
    config_initializer : Callable[..., T]
        Configuration constructor/initializer.
        Should accept **kwargs to initialize the configuration,
        e.g., Config(**kwargs).
    config_path : str | Path | None, optional (default=None)
        Path to the configuration directory containing settings.[yaml|yml|json].
        Or path to a configuration file itself.
        If None, search the current working directory for
        settings.[yaml|yml|json].
    overrides : dict[str, Any] | None, optional (default=None)
        Configuration overrides.
        Useful for overriding configuration settings programmatically,
        perhaps from CLI flags.
    set_cwd : bool, optional (default=True)
        Whether to set the current working directory to the directory
        containing the configuration file. Helpful for resolving relative paths
        in the configuration file.
    parse_env_vars : bool, optional (default=True)
        Whether to parse environment variables in the configuration text.
    load_dot_env_file : bool, optional (default=True)
        Whether to load the .env file prior to parsing environment variables.
    dot_env_path : str | Path | None, optional (default=None)
        Optional .env file to load prior to parsing env variables.
        If None and load_dot_env_file is True, looks for a .env file in the
        same directory as the config file.
    config_parser : Callable[[str], dict[str, Any]] | None, optional (default=None)
        function to parse the configuration text, (str) -> dict[str, Any].
        If None, the parser is inferred from the file extension.
        Supported extensions: .json, .yaml, .yml.
    file_encoding : str, optional (default="utf-8")
        File encoding to use when reading the configuration file.

    Returns
    -------
    T
        The initialized configuration object.

    Raises
    ------
    FileNotFoundError
        - If the config file is not found.
        - If the .env file is not found when parse_env_vars is True and dot_env_path is provided.

    ConfigParsingError
        - If an environment variable is not found when parsing env variables.
        - If there was a problem merging the overrides with the configuration.
        - If parser=None and load_config was unable to determine how to parse
        the file based on the file extension.
        - If the parser fails to parse the configuration text.
    """
    config_path = Path(config_path).resolve() if config_path else Path.cwd()
    config_path = _get_config_file_path(config_path)

    file_contents = config_path.read_text(encoding=file_encoding)

    if parse_env_vars:
        if load_dot_env_file:
            required = dot_env_path is not None
            dot_env_path = (
                Path(dot_env_path) if dot_env_path else config_path.parent / ".env"
            )
            _load_dotenv(dot_env_path, required=required)
        file_contents = _parse_env_variables(file_contents)

    if config_parser is None:
        config_parser = _get_parser_for_file(config_path)

    config_data: dict[str, Any] = {}
    try:
        config_data = config_parser(file_contents)
    except Exception as error:
        msg = f"Failed to parse config_path: {config_path}. Error: {error}"
        raise ConfigParsingError(msg) from error

    if overrides is not None:
        try:
            _recursive_merge_dicts(config_data, overrides)
        except Exception as error:
            msg = f"Failed to merge overrides with config_path: {config_path}. Error: {error}"
            raise ConfigParsingError(msg) from error

    if set_cwd:
        os.chdir(config_path.parent)

    return config_initializer(**config_data)
