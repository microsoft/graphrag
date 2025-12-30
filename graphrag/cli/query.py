# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""CLI implementation of the query subcommand."""

import asyncio
import contextlib
import io
import sys
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any

import graphrag.api as api
from graphrag.callbacks.noop_query_callbacks import NoopQueryCallbacks
from graphrag.config.load_config import load_config
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.utils.api import create_storage_from_config
from graphrag.utils.storage import load_table_from_storage, storage_has_table

if TYPE_CHECKING:
    import pandas as pd

# Suppress harmless asyncio cleanup warnings on Windows
warnings.filterwarnings("ignore", message=".*coroutine.*was never awaited")
warnings.filterwarnings("ignore", message=".*Fatal error on SSL transport.*")
warnings.filterwarnings("ignore", message=".*Event loop is closed.*")
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*coroutine.*")

# Install filtered stderr to suppress SSL cleanup errors
_original_stderr = sys.stderr


class FilteredStderr:
    """Filter stderr to suppress harmless SSL cleanup errors on Windows."""

    def __init__(self, original_stderr):
        self.original_stderr = original_stderr
        self.suppress_file_patterns = [
            "sslproto.py",
            "proactor_events.py",
        ]
        self.in_ssl_traceback = False

    def write(self, message):
        msg = message
        msg_lower = message.lower()
        
        # Detect start of SSL cleanup exception - check for "Exception ignored" or "Traceback"
        if ("exception ignored" in msg_lower or msg_lower.strip().startswith("traceback")) and \
           ("ssl" in msg_lower or "_sslprotocol" in msg_lower or any(p in msg for p in self.suppress_file_patterns)):
            self.in_ssl_traceback = True
            return
        
        # If we're in an SSL traceback, suppress everything until blank line
        if self.in_ssl_traceback:
            # Stop suppressing on blank line (end of traceback) or if we see a non-SSL error
            if message.strip() == "":
                self.in_ssl_traceback = False
            # Continue suppressing traceback lines
            return
        
        # Also suppress individual SSL/asyncio cleanup error lines that aren't in a traceback
        if any(p in msg for p in self.suppress_file_patterns) and \
           ("runtimeerror" in msg_lower or "attributeerror" in msg_lower or "fatal error" in msg_lower or "event loop is closed" in msg_lower):
            return
            
        self.original_stderr.write(message)

    def flush(self):
        self.original_stderr.flush()

    def __getattr__(self, name):
        return getattr(self.original_stderr, name)


# Install filtered stderr to suppress SSL cleanup errors during program execution
sys.stderr = FilteredStderr(_original_stderr)


def _run_async_with_cleanup(coro):
    """Run an async coroutine and suppress harmless SSL cleanup errors on Windows."""
    result = asyncio.run(coro)
    # Small delay to allow async cleanup
    try:
        asyncio.run(asyncio.sleep(0.1))
    except (RuntimeError, AttributeError):
        pass
    return result


def run_global_search(
    config_filepath: Path | None,
    data_dir: Path | None,
    root_dir: Path,
    community_level: int | None,
    dynamic_community_selection: bool,
    response_type: str,
    streaming: bool,
    query: str,
    verbose: bool,
):
    """Perform a global search with a given query.

    Loads index files required for global search and calls the Query API.
    """
    root = root_dir.resolve()
    cli_overrides = {}
    if data_dir:
        cli_overrides["output.base_dir"] = str(data_dir)
    config = load_config(root, config_filepath, cli_overrides)

    dataframe_dict = _resolve_output_files(
        config=config,
        output_list=[
            "entities",
            "communities",
            "community_reports",
        ],
        optional_list=[],
    )

    # Call the Multi-Index Global Search API
    if dataframe_dict["multi-index"]:
        final_entities_list = dataframe_dict["entities"]
        final_communities_list = dataframe_dict["communities"]
        final_community_reports_list = dataframe_dict["community_reports"]
        index_names = dataframe_dict["index_names"]

        async def run_with_cleanup():
            try:
                return await api.multi_index_global_search(
                    config=config,
                    entities_list=final_entities_list,
                    communities_list=final_communities_list,
                    community_reports_list=final_community_reports_list,
                    index_names=index_names,
                    community_level=community_level,
                    dynamic_community_selection=dynamic_community_selection,
                    response_type=response_type,
                    streaming=streaming,
                    query=query,
                    verbose=verbose,
                )
            finally:
                # Give time for async cleanup
                await asyncio.sleep(0.1)
        
        response, context_data = asyncio.run(run_with_cleanup())
        print(response)
        return response, context_data

    # Otherwise, call the Single-Index Global Search API
    final_entities: pd.DataFrame = dataframe_dict["entities"]
    final_communities: pd.DataFrame = dataframe_dict["communities"]
    final_community_reports: pd.DataFrame = dataframe_dict["community_reports"]

    if streaming:

        async def run_streaming_search():
            full_response = ""
            context_data = {}

            def on_context(context: Any) -> None:
                nonlocal context_data
                context_data = context

            callbacks = NoopQueryCallbacks()
            callbacks.on_context = on_context

            async for stream_chunk in api.global_search_streaming(
                config=config,
                entities=final_entities,
                communities=final_communities,
                community_reports=final_community_reports,
                community_level=community_level,
                dynamic_community_selection=dynamic_community_selection,
                response_type=response_type,
                query=query,
                callbacks=[callbacks],
                verbose=verbose,
            ):
                full_response += stream_chunk
                print(stream_chunk, end="")
                sys.stdout.flush()
            print()
            return full_response, context_data

        async def run_streaming_with_cleanup():
            try:
                return await run_streaming_search()
            finally:
                await asyncio.sleep(0.1)
        
        return asyncio.run(run_streaming_with_cleanup())
    # not streaming
    async def run_search_with_cleanup():
        try:
            return await api.global_search(
                config=config,
                entities=final_entities,
                communities=final_communities,
                community_reports=final_community_reports,
                community_level=community_level,
                dynamic_community_selection=dynamic_community_selection,
                response_type=response_type,
                query=query,
                verbose=verbose,
            )
        finally:
            await asyncio.sleep(0.1)
    
    response, context_data = asyncio.run(run_search_with_cleanup())
    print(response)

    return response, context_data


def run_local_search(
    config_filepath: Path | None,
    data_dir: Path | None,
    root_dir: Path,
    community_level: int,
    response_type: str,
    streaming: bool,
    query: str,
    verbose: bool,
):
    """Perform a local search with a given query.

    Loads index files required for local search and calls the Query API.
    """
    root = root_dir.resolve()
    cli_overrides = {}
    if data_dir:
        cli_overrides["output.base_dir"] = str(data_dir)
    config = load_config(root, config_filepath, cli_overrides)

    dataframe_dict = _resolve_output_files(
        config=config,
        output_list=[
            "communities",
            "community_reports",
            "text_units",
            "relationships",
            "entities",
        ],
        optional_list=[
            "covariates",
        ],
    )
    # Call the Multi-Index Local Search API
    if dataframe_dict["multi-index"]:
        final_entities_list = dataframe_dict["entities"]
        final_communities_list = dataframe_dict["communities"]
        final_community_reports_list = dataframe_dict["community_reports"]
        final_text_units_list = dataframe_dict["text_units"]
        final_relationships_list = dataframe_dict["relationships"]
        index_names = dataframe_dict["index_names"]

        # If any covariates tables are missing from any index, set the covariates list to None
        if len(dataframe_dict["covariates"]) != dataframe_dict["num_indexes"]:
            final_covariates_list = None
        else:
            final_covariates_list = dataframe_dict["covariates"]

        response, context_data = asyncio.run(
            api.multi_index_local_search(
                config=config,
                entities_list=final_entities_list,
                communities_list=final_communities_list,
                community_reports_list=final_community_reports_list,
                text_units_list=final_text_units_list,
                relationships_list=final_relationships_list,
                covariates_list=final_covariates_list,
                index_names=index_names,
                community_level=community_level,
                response_type=response_type,
                streaming=streaming,
                query=query,
                verbose=verbose,
            )
        )
        print(response)

        return response, context_data

    # Otherwise, call the Single-Index Local Search API
    final_communities: pd.DataFrame = dataframe_dict["communities"]
    final_community_reports: pd.DataFrame = dataframe_dict["community_reports"]
    final_text_units: pd.DataFrame = dataframe_dict["text_units"]
    final_relationships: pd.DataFrame = dataframe_dict["relationships"]
    final_entities: pd.DataFrame = dataframe_dict["entities"]
    final_covariates: pd.DataFrame | None = dataframe_dict["covariates"]

    if streaming:

        async def run_streaming_search():
            full_response = ""
            context_data = {}

            def on_context(context: Any) -> None:
                nonlocal context_data
                context_data = context

            callbacks = NoopQueryCallbacks()
            callbacks.on_context = on_context

            async for stream_chunk in api.local_search_streaming(
                config=config,
                entities=final_entities,
                communities=final_communities,
                community_reports=final_community_reports,
                text_units=final_text_units,
                relationships=final_relationships,
                covariates=final_covariates,
                community_level=community_level,
                response_type=response_type,
                query=query,
                callbacks=[callbacks],
                verbose=verbose,
            ):
                full_response += stream_chunk
                print(stream_chunk, end="")
                sys.stdout.flush()
            print()
            return full_response, context_data

        return asyncio.run(run_streaming_search())
    # not streaming
    response, context_data = asyncio.run(
        api.local_search(
            config=config,
            entities=final_entities,
            communities=final_communities,
            community_reports=final_community_reports,
            text_units=final_text_units,
            relationships=final_relationships,
            covariates=final_covariates,
            community_level=community_level,
            response_type=response_type,
            query=query,
            verbose=verbose,
        )
    )
    print(response)

    return response, context_data


def run_drift_search(
    config_filepath: Path | None,
    data_dir: Path | None,
    root_dir: Path,
    community_level: int,
    response_type: str,
    streaming: bool,
    query: str,
    verbose: bool,
):
    """Perform a local search with a given query.

    Loads index files required for local search and calls the Query API.
    """
    root = root_dir.resolve()
    cli_overrides = {}
    if data_dir:
        cli_overrides["output.base_dir"] = str(data_dir)
    config = load_config(root, config_filepath, cli_overrides)

    dataframe_dict = _resolve_output_files(
        config=config,
        output_list=[
            "communities",
            "community_reports",
            "text_units",
            "relationships",
            "entities",
        ],
    )

    # Call the Multi-Index Drift Search API
    if dataframe_dict["multi-index"]:
        final_entities_list = dataframe_dict["entities"]
        final_communities_list = dataframe_dict["communities"]
        final_community_reports_list = dataframe_dict["community_reports"]
        final_text_units_list = dataframe_dict["text_units"]
        final_relationships_list = dataframe_dict["relationships"]
        index_names = dataframe_dict["index_names"]

        response, context_data = asyncio.run(
            api.multi_index_drift_search(
                config=config,
                entities_list=final_entities_list,
                communities_list=final_communities_list,
                community_reports_list=final_community_reports_list,
                text_units_list=final_text_units_list,
                relationships_list=final_relationships_list,
                index_names=index_names,
                community_level=community_level,
                response_type=response_type,
                streaming=streaming,
                query=query,
                verbose=verbose,
            )
        )
        print(response)

        return response, context_data

    # Otherwise, call the Single-Index Drift Search API
    final_communities: pd.DataFrame = dataframe_dict["communities"]
    final_community_reports: pd.DataFrame = dataframe_dict["community_reports"]
    final_text_units: pd.DataFrame = dataframe_dict["text_units"]
    final_relationships: pd.DataFrame = dataframe_dict["relationships"]
    final_entities: pd.DataFrame = dataframe_dict["entities"]

    if streaming:

        async def run_streaming_search():
            full_response = ""
            context_data = {}

            def on_context(context: Any) -> None:
                nonlocal context_data
                context_data = context

            callbacks = NoopQueryCallbacks()
            callbacks.on_context = on_context

            async for stream_chunk in api.drift_search_streaming(
                config=config,
                entities=final_entities,
                communities=final_communities,
                community_reports=final_community_reports,
                text_units=final_text_units,
                relationships=final_relationships,
                community_level=community_level,
                response_type=response_type,
                query=query,
                callbacks=[callbacks],
                verbose=verbose,
            ):
                full_response += stream_chunk
                print(stream_chunk, end="")
                sys.stdout.flush()
            print()
            return full_response, context_data

        return asyncio.run(run_streaming_search())

    # not streaming
    response, context_data = asyncio.run(
        api.drift_search(
            config=config,
            entities=final_entities,
            communities=final_communities,
            community_reports=final_community_reports,
            text_units=final_text_units,
            relationships=final_relationships,
            community_level=community_level,
            response_type=response_type,
            query=query,
            verbose=verbose,
        )
    )
    print(response)

    return response, context_data


def run_basic_search(
    config_filepath: Path | None,
    data_dir: Path | None,
    root_dir: Path,
    streaming: bool,
    query: str,
    verbose: bool,
):
    """Perform a basics search with a given query.

    Loads index files required for basic search and calls the Query API.
    """
    root = root_dir.resolve()
    cli_overrides = {}
    if data_dir:
        cli_overrides["output.base_dir"] = str(data_dir)
    config = load_config(root, config_filepath, cli_overrides)

    dataframe_dict = _resolve_output_files(
        config=config,
        output_list=[
            "text_units",
        ],
    )

    # Call the Multi-Index Basic Search API
    if dataframe_dict["multi-index"]:
        final_text_units_list = dataframe_dict["text_units"]
        index_names = dataframe_dict["index_names"]

        response, context_data = _run_async_with_cleanup(
            api.multi_index_basic_search(
                config=config,
                text_units_list=final_text_units_list,
                index_names=index_names,
                streaming=streaming,
                query=query,
                verbose=verbose,
            )
        )
        print(response)

        return response, context_data

    # Otherwise, call the Single-Index Basic Search API
    final_text_units: pd.DataFrame = dataframe_dict["text_units"]

    if streaming:

        async def run_streaming_search():
            full_response = ""
            context_data = {}

            def on_context(context: Any) -> None:
                nonlocal context_data
                context_data = context

            callbacks = NoopQueryCallbacks()
            callbacks.on_context = on_context

            async for stream_chunk in api.basic_search_streaming(
                config=config,
                text_units=final_text_units,
                query=query,
                callbacks=[callbacks],
                verbose=verbose,
            ):
                full_response += stream_chunk
                print(stream_chunk, end="")
                sys.stdout.flush()
            print()
            return full_response, context_data

        return asyncio.run(run_streaming_search())
    # not streaming
    response, context_data = _run_async_with_cleanup(
        api.basic_search(
            config=config,
            text_units=final_text_units,
            query=query,
            verbose=verbose,
        )
    )
    print(response)

    return response, context_data


def _resolve_output_files(
    config: GraphRagConfig,
    output_list: list[str],
    optional_list: list[str] | None = None,
) -> dict[str, Any]:
    """Read indexing output files to a dataframe dict."""
    dataframe_dict = {}

    # Loading output files for multi-index search
    if config.outputs:
        dataframe_dict["multi-index"] = True
        dataframe_dict["num_indexes"] = len(config.outputs)
        dataframe_dict["index_names"] = config.outputs.keys()
        for output in config.outputs.values():
            storage_obj = create_storage_from_config(output)
            for name in output_list:
                if name not in dataframe_dict:
                    dataframe_dict[name] = []
                df_value = asyncio.run(
                    load_table_from_storage(name=name, storage=storage_obj)
                )
                dataframe_dict[name].append(df_value)

            # for optional output files, do not append if the dataframe does not exist
            if optional_list:
                for optional_file in optional_list:
                    if optional_file not in dataframe_dict:
                        dataframe_dict[optional_file] = []
                    file_exists = asyncio.run(
                        storage_has_table(optional_file, storage_obj)
                    )
                    if file_exists:
                        df_value = asyncio.run(
                            load_table_from_storage(
                                name=optional_file, storage=storage_obj
                            )
                        )
                        dataframe_dict[optional_file].append(df_value)
        return dataframe_dict
    # Loading output files for single-index search
    dataframe_dict["multi-index"] = False
    storage_obj = create_storage_from_config(config.output)
    for name in output_list:
        df_value = asyncio.run(load_table_from_storage(name=name, storage=storage_obj))
        dataframe_dict[name] = df_value

    # for optional output files, set the dict entry to None instead of erroring out if it does not exist
    if optional_list:
        for optional_file in optional_list:
            file_exists = asyncio.run(storage_has_table(optional_file, storage_obj))
            if file_exists:
                df_value = asyncio.run(
                    load_table_from_storage(name=optional_file, storage=storage_obj)
                )
                dataframe_dict[optional_file] = df_value
            else:
                dataframe_dict[optional_file] = None
    return dataframe_dict
