# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""Parameterization settings for the default configuration, loaded from environment variables."""

from pathlib import Path
from typing import Any

from environs import Env


class ConfigSection:
    """The default configuration section for TextEmbedding, loaded from environment variables."""

    _env: Env

    def __init__(self, env: Env):
        """Create a new instance of the parameters class."""
        self._env = env

    def replace_dict(self, values: dict | None) -> dict | None:
        """Replace the values in the dictionary."""
        if values is None:
            return None
        result = {**values}
        for k, v in result.items():
            if isinstance(v, dict):
                result[k] = self.replace_dict(v)
            else:
                result[k] = self.replace(v)
        return result

    def readopt(self, values: dict, key: str, default_value: Any = None) -> Any:
        """Read the options from the given dictionary."""
        result = values.get(key, default_value)
        return self.replace(result, default_value)

    def replace(self, value: Any, default_value: Any = None) -> Any:
        """Replace the value with the environment variable."""
        if value is None:
            return default_value

        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var_name = value[2:-1]
            if isinstance(default_value, int):
                value = self._env.int(env_var_name, default_value)
            if isinstance(default_value, float):
                value = self._env.float(env_var_name, default_value)
            if isinstance(default_value, bool):
                value = self._env.bool(env_var_name, default_value)
            if isinstance(default_value, list):
                value = self._env(env_var_name, default_value)
                value = _array_string(value)
            else:
                value = self._env(env_var_name, value)

        return value


def read_text_file(root_dir: str, text_file: str | None) -> str | None:
    """Read a text file and return the contents as a string."""
    if text_file is None:
        return None

    with (Path(root_dir) / text_file).open() as f:
        return f.read()


def _array_string(raw: str | None, default_value: list[str] | None = None) -> list[str]:
    """Filter the array entries."""
    if raw is None:
        return default_value if default_value is not None else []

    result = [r.strip() for r in raw.split(",")]
    return [r for r in result if r != ""]
