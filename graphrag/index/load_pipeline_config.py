# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing read_dotenv, load_pipeline_config, _parse_yaml and _create_include_constructor methods definition."""

import json
from pathlib import Path

import yaml
from pyaml_env import parse_config as parse_config_with_env

from graphrag.config.create_graphrag_config import create_graphrag_config, read_dotenv
from graphrag.index.config.pipeline import PipelineConfig
from graphrag.index.create_pipeline_config import create_pipeline_config


def load_pipeline_config(config_or_path: str | PipelineConfig) -> PipelineConfig:
    """Load a pipeline config from a file path or a config object."""
    if isinstance(config_or_path, PipelineConfig):
        config = config_or_path
    elif config_or_path == "default":
        config = create_pipeline_config(create_graphrag_config(root_dir="."))
    else:
        # Is there a .env file in the same directory as the config?
        read_dotenv(str(Path(config_or_path).parent))

        if config_or_path.endswith(".json"):
            with Path(config_or_path).open("rb") as f:
                config = json.loads(f.read().decode(encoding="utf-8", errors="strict"))
        elif config_or_path.endswith((".yml", ".yaml")):
            config = _parse_yaml(config_or_path)
        else:
            msg = f"Invalid config file type: {config_or_path}"
            raise ValueError(msg)

        config = PipelineConfig.model_validate(config)
        if not config.root_dir:
            config.root_dir = str(Path(config_or_path).parent.resolve())

    if config.extends is not None:
        if isinstance(config.extends, str):
            config.extends = [config.extends]
        for extended_config in config.extends:
            extended_config = load_pipeline_config(extended_config)
            merged_config = {
                **json.loads(extended_config.model_dump_json()),
                **json.loads(config.model_dump_json(exclude_unset=True)),
            }
            config = PipelineConfig.model_validate(merged_config)

    return config


def _parse_yaml(path: str):
    """Parse a yaml file, with support for !include directives."""
    # I don't like that this is static
    loader_class = yaml.SafeLoader

    # Add !include constructor if not already present.
    if "!include" not in loader_class.yaml_constructors:
        loader_class.add_constructor("!include", _create_include_constructor())

    return parse_config_with_env(path, loader=loader_class, default_value="")


def _create_include_constructor():
    """Create a constructor for !include directives."""

    def handle_include(loader: yaml.Loader, node: yaml.Node):
        """Include file referenced at node."""
        filename = str(Path(loader.name).parent / node.value)
        if filename.endswith((".yml", ".yaml")):
            return _parse_yaml(filename)

        with Path(filename).open("rb") as f:
            return f.read().decode(encoding="utf-8", errors="strict")

    return handle_include
