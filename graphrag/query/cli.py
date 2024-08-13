# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Command line interface for the query module."""

import asyncio
import re
from pathlib import Path
from typing import cast

import pandas as pd

from graphrag.config import (
    GraphRagConfig,
    create_graphrag_config,
)
from graphrag.index.progress import PrintProgressReporter

from . import api

reporter = PrintProgressReporter("")


def run_global_search(
    config_dir: str | None,
    data_dir: str | None,
    root_dir: str | None,
    community_level: int,
    response_type: str,
    query: str,
):
    """Perform a global search with a given query.

    Loads index files required for global search and calls the Query API.
    """
    data_dir, root_dir, config = _configure_paths_and_settings(
        data_dir, root_dir, config_dir
    )
    data_path = Path(data_dir)

    final_nodes: pd.DataFrame = pd.read_parquet(
        data_path / "create_final_nodes.parquet"
    )
    final_entities: pd.DataFrame = pd.read_parquet(
        data_path / "create_final_entities.parquet"
    )
    final_community_reports: pd.DataFrame = pd.read_parquet(
        data_path / "create_final_community_reports.parquet"
    )

    return asyncio.run(
        api.global_search(
            config=config,
            nodes=final_nodes,
            entities=final_entities,
            community_reports=final_community_reports,
            community_level=community_level,
            response_type=response_type,
            query=query,
        )
    )


def run_local_search(
    config_dir: str | None,
    data_dir: str | None,
    root_dir: str | None,
    community_level: int,
    response_type: str,
    query: str,
):
    """Perform a local search with a given query.

    Loads index files required for local search and calls the Query API.
    """
    data_dir, root_dir, config = _configure_paths_and_settings(
        data_dir, root_dir, config_dir
    )
    data_path = Path(data_dir)

    final_nodes = pd.read_parquet(data_path / "create_final_nodes.parquet")
    final_community_reports = pd.read_parquet(
        data_path / "create_final_community_reports.parquet"
    )
    final_text_units = pd.read_parquet(data_path / "create_final_text_units.parquet")
    final_relationships = pd.read_parquet(
        data_path / "create_final_relationships.parquet"
    )
    final_entities = pd.read_parquet(data_path / "create_final_entities.parquet")
    final_covariates_path = data_path / "create_final_covariates.parquet"
    final_covariates = (
        pd.read_parquet(final_covariates_path)
        if final_covariates_path.exists()
        else None
    )

    # call the Query API
    return asyncio.run(
        api.local_search(
            config=config,
            nodes=final_nodes,
            entities=final_entities,
            community_reports=final_community_reports,
            text_units=final_text_units,
            relationships=final_relationships,
            covariates=final_covariates,
            community_level=community_level,
            response_type=response_type,
            query=query,
        )
    )


def _configure_paths_and_settings(
    data_dir: str | None,
    root_dir: str | None,
    config_dir: str | None,
) -> tuple[str, str | None, GraphRagConfig]:
    if data_dir is None and root_dir is None:
        msg = "Either data_dir or root_dir must be provided."
        raise ValueError(msg)
    if data_dir is None:
        data_dir = _infer_data_dir(cast(str, root_dir))
    config = _create_graphrag_config(root_dir, config_dir)
    return data_dir, root_dir, config


def _infer_data_dir(root: str) -> str:
    output = Path(root) / "output"
    # use the latest data-run folder
    if output.exists():
        expr = re.compile(r"\d{8}-\d{6}")
        filtered = [f for f in output.iterdir() if f.is_dir() and expr.match(f.name)]
        folders = sorted(filtered, key=lambda f: f.name, reverse=True)
        if len(folders) > 0:
            folder = folders[0]
            return str((folder / "artifacts").absolute())
    msg = f"Could not infer data directory from root={root}"
    raise ValueError(msg)


def _create_graphrag_config(
    root: str | None,
    config_dir: str | None,
) -> GraphRagConfig:
    """Create a GraphRag configuration."""
    return _read_config_parameters(root or "./", config_dir)


def _read_config_parameters(root: str, config: str | None):
    _root = Path(root)
    settings_yaml = (
        Path(config)
        if config and Path(config).suffix in [".yaml", ".yml"]
        else _root / "settings.yaml"
    )
    if not settings_yaml.exists():
        settings_yaml = _root / "settings.yml"

    if settings_yaml.exists():
        reporter.info(f"Reading settings from {settings_yaml}")
        with settings_yaml.open(
            "rb",
        ) as file:
            import yaml

            data = yaml.safe_load(file.read().decode(encoding="utf-8", errors="strict"))
            return create_graphrag_config(data, root)

    settings_json = (
        Path(config)
        if config and Path(config).suffix == ".json"
        else _root / "settings.json"
    )
    if settings_json.exists():
        reporter.info(f"Reading settings from {settings_json}")
        with settings_json.open("rb") as file:
            import json

            data = json.loads(file.read().decode(encoding="utf-8", errors="strict"))
            return create_graphrag_config(data, root)

    reporter.info("Reading settings from environment variables")
    return create_graphrag_config(root_dir=root)
