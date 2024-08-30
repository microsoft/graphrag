# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Command line interface for the query module."""

import asyncio
import re
import sys
from pathlib import Path

import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobClient

from graphrag.config import (
    GraphRagConfig,
    StorageType,
    create_graphrag_config,
)
from graphrag.config.resolve_timestamp_path import resolve_timestamp_path
from graphrag.index.progress import PrintProgressReporter

from . import api

reporter = PrintProgressReporter("")


def run_global_search(
    config_filepath: str | None,
    data_dir: str | None,
    root_dir: str | None,
    community_level: int,
    response_type: str,
    streaming: bool,
    query: str,
):
    """Perform a global search with a given query.

    Loads index files required for global search and calls the Query API.
    """
    data_dir, root_dir, config = _configure_paths_and_settings(
        data_dir, root_dir, config_filepath
    )
    data_path = Path(data_dir)

    dataframe_dict = _resolve_parquet_files(
        data_path=data_path,
        config=config
    )
    final_nodes: pd.DataFrame = dataframe_dict["nodes"]
    final_entities: pd.DataFrame = dataframe_dict["entities"]
    final_community_reports: pd.DataFrame = dataframe_dict["community_reports"]

    # call the Query API
    if streaming:

        async def run_streaming_search():
            full_response = ""
            context_data = None
            get_context_data = True
            async for stream_chunk in api.global_search_streaming(
                config=config,
                nodes=final_nodes,
                entities=final_entities,
                community_reports=final_community_reports,
                community_level=community_level,
                response_type=response_type,
                query=query,
            ):
                if get_context_data:
                    context_data = stream_chunk
                    get_context_data = False
                else:
                    full_response += stream_chunk
                    print(stream_chunk, end="")  # noqa: T201
                    sys.stdout.flush()  # flush output buffer to display text immediately
            print()  # noqa: T201
            return full_response, context_data

        return asyncio.run(run_streaming_search())
    # not streaming
    response, context_data = asyncio.run(
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
    reporter.success(f"Global Search Response:\n{response}")
    # NOTE: we return the response and context data here purely as a complete demonstration of the API.
    # External users should use the API directly to get the response and context data.
    return response, context_data


def run_local_search(
    config_filepath: str | None,
    data_dir: str | None,
    root_dir: str | None,
    community_level: int,
    response_type: str,
    streaming: bool,
    query: str,
):
    """Perform a local search with a given query.

    Loads index files required for local search and calls the Query API.
    """
    data_dir, root_dir, config = _configure_paths_and_settings(
        data_dir, root_dir, config_filepath
    )
    data_path = Path(data_dir)

    dataframe_dict = _resolve_parquet_files(
        data_path=data_path,
        config=config
    )
    final_nodes: pd.DataFrame = dataframe_dict["nodes"]
    final_community_reports: pd.DataFrame = dataframe_dict["community_reports"]
    final_text_units: pd.DataFrame = dataframe_dict["text_units"]
    final_relationships: pd.DataFrame = dataframe_dict["relationships"]
    final_entities: pd.DataFrame = dataframe_dict["entities"]
    final_covariates: pd.DataFrame | None = dataframe_dict["covariates"]
    # call the Query API
    if streaming:

        async def run_streaming_search():
            full_response = ""
            context_data = None
            get_context_data = True
            async for stream_chunk in api.local_search_streaming(
                root_dir=root_dir,
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
            ):
                if get_context_data:
                    context_data = stream_chunk
                    get_context_data = False
                else:
                    full_response += stream_chunk
                    print(stream_chunk, end="")  # noqa: T201
                    sys.stdout.flush()  # flush output buffer to display text immediately
            print()  # noqa: T201
            return full_response, context_data

        return asyncio.run(run_streaming_search())
    # not streaming
    response, context_data = asyncio.run(
        api.local_search(
            root_dir=root_dir,
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
    reporter.success(f"Local Search Response:\n{response}")
    # NOTE: we return the response and context data here purely as a complete demonstration of the API.
    # External users should use the API directly to get the response and context data.
    return response, context_data


def _configure_paths_and_settings(
    data_dir: str | None,
    root_dir: str | None,
    config_filepath: str | None,
) -> tuple[str, str | None, GraphRagConfig]:
    config = _create_graphrag_config(root_dir, config_filepath)
    if data_dir is None and root_dir is None:
        msg = "Either data_dir or root_dir must be provided."
        raise ValueError(msg)
    if data_dir is None:
        base_dir = Path(str(root_dir)) / config.storage.base_dir
        data_dir = str(resolve_timestamp_path(base_dir))
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

def _resolve_parquet_files(
    data_path: Path,
    config: GraphRagConfig
) -> dict[str, pd.DataFrame]:
    """Read parquet files to a dataframe dict."""
    dataframe_dict = {}
    match config.storage.type:
        case StorageType.blob:
            if config.storage.container_name is None:
                msg = "Container name required for querying from blob storage"
                raise ValueError(msg)
            if (
                config.storage.connection_string is None
                and config.storage.storage_account_blob_url is None
            ):
                msg = "Connection string or storage account blob url required for querying blob storage"
                raise ValueError(msg)
            storage_account_blob_url = config.storage.storage_account_blob_url
            storage_account_name = (
                storage_account_blob_url.split("//")[1].split(".")[0]
                if storage_account_blob_url
                else None
            )
            storage_options = {
                "account_name": storage_account_name,
                "account_host": storage_account_blob_url,
                "credential": DefaultAzureCredential(),
            }
            container_name = config.storage.container_name
            base_dir = config.storage.base_dir
            dataframe_dict["nodes"] = pd.read_parquet(
                f"abfs://{container_name}/{base_dir}/create_final_nodes.parquet",
                storage_options=storage_options
            )
            dataframe_dict["entities"] = pd.read_parquet(
                f"abfs://{container_name}/{base_dir}/create_final_entities.parquet",
                storage_options=storage_options
            )
            dataframe_dict["community_reports"] = pd.read_parquet(
                f"abfs://{container_name}/{base_dir}/create_final_community_reports.parquet",
                storage_options=storage_options
            )
            dataframe_dict["text_units"] = pd.read_parquet(
                f"abfs://{container_name}/{base_dir}/create_final_text_units.parquet",
                storage_options=storage_options
            )
            dataframe_dict["relationships"] = pd.read_parquet(
                f"abfs://{container_name}/{base_dir}/create_final_relationships.parquet",
                storage_options=storage_options
            )
            final_covariates_blob = BlobClient.from_blob_url(
                f"{storage_account_blob_url}/{container_name}/{base_dir}/create_final_covariates.parquet"
            )
            dataframe_dict["covariates"] = (
                pd.read_parquet(
                    f"abfs://{container_name}/{base_dir}/create_final_covariates.parquet",
                    storage_options=storage_options
                )
                if final_covariates_blob.exists()
                else None
            )
        case StorageType.file:
            dataframe_dict["nodes"] = pd.read_parquet(data_path / "create_final_nodes.parquet")
            dataframe_dict["entities"] = pd.read_parquet(data_path / "create_final_entities.parquet")
            dataframe_dict["community_reports"] = pd.read_parquet(data_path / "create_final_community_reports.parquet")
            dataframe_dict["text_units"] = pd.read_parquet(data_path / "create_final_text_units.parquet")
            dataframe_dict["relationships"] = pd.read_parquet(data_path / "create_final_relationships.parquet")

            final_covariates_path = data_path / "create_final_covariates.parquet"
            dataframe_dict["covariates"] = (
                pd.read_parquet(final_covariates_path)
                if final_covariates_path.exists()
                else None
            )
        case _:
            dataframe_dict["nodes"] = pd.read_parquet(data_path / "create_final_nodes.parquet")
            dataframe_dict["entities"] = pd.read_parquet(data_path / "create_final_entities.parquet")
            dataframe_dict["community_reports"] = pd.read_parquet(data_path / "create_final_community_reports.parquet")
            dataframe_dict["text_units"] = pd.read_parquet(data_path / "create_final_text_units.parquet")
            dataframe_dict["relationships"] = pd.read_parquet(data_path / "create_final_relationships.parquet")

            final_covariates_path = data_path / "create_final_covariates.parquet"
            dataframe_dict["covariates"] = (
                pd.read_parquet(final_covariates_path)
                if final_covariates_path.exists()
                else None
            )
    return dataframe_dict

def _create_graphrag_config(
    root: str | None,
    config_filepath: str | None,
) -> GraphRagConfig:
    """Create a GraphRag configuration."""
    return _read_config_parameters(root or "./", config_filepath)


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
