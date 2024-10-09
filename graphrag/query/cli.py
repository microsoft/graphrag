# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Command line interface for the query module."""

import asyncio
import sys
from pathlib import Path

import pandas as pd

from graphrag.config import GraphRagConfig, load_config, resolve_paths
from graphrag.index.create_pipeline_config import create_pipeline_config
from graphrag.index.progress import PrintProgressReporter
from graphrag.utils.storage import _create_storage, _load_table_from_storage

from . import api

reporter = PrintProgressReporter("")


def run_global_search(
    config_filepath: str | None,
    data_dir: str | None,
    root_dir: str,
    community_level: int,
    response_type: str,
    streaming: bool,
    query: str,
):
    """Perform a global search with a given query.

    Loads index files required for global search and calls the Query API.
    """
    root = Path(root_dir).resolve()
    config = load_config(root, config_filepath)

    config.storage.base_dir = data_dir or config.storage.base_dir
    resolve_paths(config)

    dataframe_dict = _resolve_parquet_files(
        root_dir=root_dir,
        config=config,
        parquet_list=[
            "create_final_nodes.parquet",
            "create_final_entities.parquet",
            "create_final_community_reports.parquet",
        ],
        optional_list=[],
    )
    final_nodes: pd.DataFrame = dataframe_dict["create_final_nodes"]
    final_entities: pd.DataFrame = dataframe_dict["create_final_entities"]
    final_community_reports: pd.DataFrame = dataframe_dict[
        "create_final_community_reports"
    ]

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
    root_dir: str,
    community_level: int,
    response_type: str,
    streaming: bool,
    query: str,
):
    """Perform a local search with a given query.

    Loads index files required for local search and calls the Query API.
    """
    root = Path(root_dir).resolve()
    config = load_config(root, config_filepath)

    config.storage.base_dir = data_dir or config.storage.base_dir
    resolve_paths(config)

    dataframe_dict = _resolve_parquet_files(
        root_dir=root_dir,
        config=config,
        parquet_list=[
            "create_final_nodes.parquet",
            "create_final_community_reports.parquet",
            "create_final_text_units.parquet",
            "create_final_relationships.parquet",
            "create_final_entities.parquet",
        ],
        optional_list=["create_final_covariates.parquet"],
    )
    final_nodes: pd.DataFrame = dataframe_dict["create_final_nodes"]
    final_community_reports: pd.DataFrame = dataframe_dict[
        "create_final_community_reports"
    ]
    final_text_units: pd.DataFrame = dataframe_dict["create_final_text_units"]
    final_relationships: pd.DataFrame = dataframe_dict["create_final_relationships"]
    final_entities: pd.DataFrame = dataframe_dict["create_final_entities"]
    final_covariates: pd.DataFrame | None = dataframe_dict["create_final_covariates"]

    # call the Query API
    if streaming:

        async def run_streaming_search():
            full_response = ""
            context_data = None
            get_context_data = True
            async for stream_chunk in api.local_search_streaming(
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


def _resolve_parquet_files(
    root_dir: str,
    config: GraphRagConfig,
    parquet_list: list[str],
    optional_list: list[str],
) -> dict[str, pd.DataFrame]:
    """Read parquet files to a dataframe dict."""
    dataframe_dict = {}
    pipeline_config = create_pipeline_config(config)
    storage_obj = _create_storage(root_dir=root_dir, config=pipeline_config.storage)
    for parquet_file in parquet_list:
        df_key = parquet_file.split(".")[0]
        df_value = asyncio.run(
            _load_table_from_storage(name=parquet_file, storage=storage_obj)
        )
        dataframe_dict[df_key] = df_value

    # for optional parquet files, set the dict entry to None instead of erroring out if it does not exist
    for optional_file in optional_list:
        file_exists = asyncio.run(storage_obj.has(optional_file))
        df_key = optional_file.split(".")[0]
        if file_exists:
            df_value = asyncio.run(
                _load_table_from_storage(name=optional_file, storage=storage_obj)
            )
            dataframe_dict[df_key] = df_value
        else:
            dataframe_dict[df_key] = None

    return dataframe_dict
