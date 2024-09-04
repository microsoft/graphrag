# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Command line interface for the query module."""

import asyncio
import sys
from pathlib import Path

import pandas as pd

from graphrag.config import load_config, resolve_path
from graphrag.index.progress import PrintProgressReporter

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

    if data_dir:
        config.storage.base_dir = str(resolve_path(data_dir, root))

    data_path = Path(config.storage.base_dir).resolve()

    final_nodes: pd.DataFrame = pd.read_parquet(
        data_path / "create_final_nodes.parquet"
    )
    final_entities: pd.DataFrame = pd.read_parquet(
        data_path / "create_final_entities.parquet"
    )
    final_community_reports: pd.DataFrame = pd.read_parquet(
        data_path / "create_final_community_reports.parquet"
    )

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

    if data_dir:
        config.storage.base_dir = str(resolve_path(data_dir, root))

    data_path = Path(config.storage.base_dir).resolve()

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
