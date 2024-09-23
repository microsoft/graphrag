# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Config loading, parsing and handling module."""

from pathlib import Path

from graphrag.config import create_graphrag_config
from graphrag.index.progress.types import ProgressReporter


def read_config_parameters(root: str, reporter: ProgressReporter):
    """Read the configuration parameters from the settings file or environment variables.

    Parameters
    ----------
    - root: The root directory where the parameters are.
    - reporter: The progress reporter.
    """
    _root = Path(root)
    settings_yaml = _root / "settings.yaml"
    if not settings_yaml.exists():
        settings_yaml = _root / "settings.yml"
    settings_json = _root / "settings.json"

    if settings_yaml.exists():
        reporter.info(f"Reading settings from {settings_yaml}")
        with settings_yaml.open("rb") as file:
            import yaml

            data = yaml.safe_load(file.read().decode(encoding="utf-8", errors="strict"))
            return create_graphrag_config(data, root)

    if settings_json.exists():
        reporter.info(f"Reading settings from {settings_json}")
        with settings_json.open("rb") as file:
            import json

            data = json.loads(file.read().decode(encoding="utf-8", errors="strict"))
            return create_graphrag_config(data, root)

    reporter.info("Reading settings from environment variables")
    return create_graphrag_config(root_dir=root)
