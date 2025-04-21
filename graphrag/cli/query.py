# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""CLI implementation of the query subcommand."""

import asyncio
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import graphrag.api as api
from graphrag.callbacks.noop_query_callbacks import NoopQueryCallbacks
from graphrag.config.load_config import load_config
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.logger.print_progress import PrintProgressLogger
from graphrag.utils.api import create_storage_from_config
from graphrag.utils.storage import load_table_from_storage, storage_has_table

if TYPE_CHECKING:
    import pandas as pd

logger = PrintProgressLogger("")

class RawChunksCallback(NoopQueryCallbacks):
    def on_context(self, context: Any) -> None:
        try:
            # For DRIFT search's three-step process
            if isinstance(context, dict) and 'initial_context' in context:
                print("\n=== DRIFT SEARCH RAW CHUNKS ===")
                
                # Step 1: Primer Search
                print("\nSTEP 1 - PRIMER SEARCH:")
                if hasattr(context['initial_context'], 'context_chunks'):
                    chunks = context['initial_context'].context_chunks
                    if isinstance(chunks, dict) and 'reports' in chunks:
                        for i, report in enumerate(chunks['reports'], 1):
                            print(f"\nReport {i}:")
                            print(f"Title: {report.get('title', 'N/A')}")
                            print(f"Text: {report.get('text', 'N/A')}")
                    else:
                        print(chunks)
                
                # Step 2: Follow-up Searches
                print("\nSTEP 2 - FOLLOW-UP SEARCHES:")
                if 'followup_contexts' in context:
                    for i, followup in enumerate(context['followup_contexts'], 1):
                        print(f"\nFollow-up {i}:")
                        if hasattr(followup, 'query'):
                            print(f"Question: {followup.query}")
                        if hasattr(followup, 'context_chunks'):
                            print("Retrieved Context:")
                            if isinstance(followup.context_chunks, dict):
                                for key, value in followup.context_chunks.items():
                                    print(f"\n{key}: {value}")
                            else:
                                print(followup.context_chunks)
                
                # Step 3: Final Synthesis
                print("\nSTEP 3 - FINAL SYNTHESIS:")
                if 'final_context' in context and hasattr(context['final_context'], 'context_chunks'):
                    final_chunks = context['final_context'].context_chunks
                    if isinstance(final_chunks, dict):
                        for key, value in final_chunks.items():
                            print(f"\n{key}: {value}")
                    else:
                        print(final_chunks)
                
                print("\n=== END DRIFT SEARCH RAW CHUNKS ===\n")
                
                  
            # For Global and Local searches
            else:
                print("\n=== RAW CHUNKS FROM VECTOR STORE ===")
                
                # First try to access context_records if available
                if hasattr(context, 'context_records'):
                    records = context.context_records
                    if isinstance(records, dict):
                        # Handle reports
                        if 'reports' in records:
                            print("\nReports:")
                            for i, report in enumerate(records['reports'], 1):
                                print(f"\nReport {i}:")
                                if isinstance(report, dict):
                                    if 'title' in report:
                                        print(f"Title: {report['title']}")
                                    if 'text' in report:
                                        print(f"Text: {report['text']}")
                                    if 'content' in report:
                                        print(f"Content: {report['content']}")
                        
                        # Handle text units
                        if 'text_units' in records:
                            print("\nText Units:")
                            for i, unit in enumerate(records['text_units'], 1):
                                print(f"\nText Unit {i}:")
                                if isinstance(unit, dict):
                                    if 'text' in unit:
                                        print(f"Text: {unit['text']}")
                                    if 'source' in unit:
                                        print(f"Source: {unit['source']}")
                        
                        # Handle relationships
                        if 'relationships' in records:
                            print("\nRelationships:")
                            for i, rel in enumerate(records['relationships'], 1):
                                print(f"\nRelationship {i}: {rel}")
                
                # Fallback to direct attributes if context_records not available
                else:
                    # Handle reports
                    if hasattr(context, 'reports'):
                        print("\nReports:")
                        for i, report in enumerate(context.reports, 1):
                            print(f"\nReport {i}:")
                            if isinstance(report, dict):
                                if 'title' in report:
                                    print(f"Title: {report['title']}")
                                if 'text' in report:
                                    print(f"Text: {report['text']}")
                                if 'content' in report:
                                    print(f"Content: {report['content']}")
                    
                    # Handle text units
                    if hasattr(context, 'text_units'):
                        print("\nText Units:")
                        for i, unit in enumerate(context.text_units, 1):
                            print(f"\nText Unit {i}:")
                            if isinstance(unit, dict):
                                if 'text' in unit:
                                    print(f"Text: {unit['text']}")
                                if 'source' in unit:
                                    print(f"Source: {unit['source']}")
                    
                    # Handle relationships
                    if hasattr(context, 'relationships'):
                        print("\nRelationships:")
                        for i, rel in enumerate(context.relationships, 1):
                            print(f"\nRelationship {i}: {rel}")
                
                # Final fallback to context_chunks
                if not (hasattr(context, 'context_records') or 
                       hasattr(context, 'reports') or 
                       hasattr(context, 'text_units') or 
                       hasattr(context, 'relationships')):
                    if hasattr(context, 'context_chunks'):
                        print("\nContext Chunks:")
                        chunks = context.context_chunks
                        if isinstance(chunks, dict):
                            for key, value in chunks.items():
                                print(f"\n{key}:")
                                if isinstance(value, list):
                                    for i, item in enumerate(value, 1):
                                        if isinstance(item, dict):
                                            print(f"\nItem {i}:")
                                            for k, v in item.items():
                                                print(f"{k}: {v}")
                                        else:
                                            print(f"\nItem {i}: {item}")
                                else:
                                    print(value)
                        elif isinstance(chunks, list):
                            for i, chunk in enumerate(chunks, 1):
                                if isinstance(chunk, dict):
                                    print(f"\nChunk {i}:")
                                    for k, v in chunk.items():
                                        print(f"{k}: {v}")
                                else:
                                    print(f"\nChunk {i}: {chunk}")
                
                # If nothing was found, print debug info
                if not any([hasattr(context, attr) for attr in ['context_records', 'reports', 'text_units', 'relationships', 'context_chunks']]):
                    # print("\nDebug Info:")
                    # print(f"Context type: {type(context)}")
                    # print(f"Available attributes: {dir(context)}")
                    print(f"Raw context: {context}")
                
                print("\n=== END RAW CHUNKS ===\n")
                
        except Exception as e:
            print(f"\nError displaying chunks: {str(e)}")
            print(f"Context type: {type(context)}")
            print(f"Context attributes: {dir(context)}")
            
            
def run_global_search(
    config_filepath: Path | None,
    data_dir: Path | None,
    root_dir: Path,
    community_level: int | None,
    dynamic_community_selection: bool,
    response_type: str,
    streaming: bool,
    query: str,
    raw_chunks: bool = False 
):
    """Perform a global search with a given query.

    Loads index files required for global search and calls the Query API.
    """
    #print(f"\nDEBUG: run_global_search called with raw_chunks={raw_chunks}")
    
    root = root_dir.resolve()
    cli_overrides = {}
    if data_dir:
        cli_overrides["output.base_dir"] = str(data_dir)
    config = load_config(root, config_filepath, cli_overrides)
    
     # Initialize callbacks list
    callbacks = []
    if raw_chunks:
        callbacks.append(RawChunksCallback())

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

        logger.success(
            f"Running Multi-index Global Search: {dataframe_dict['index_names']}"
        )

        response, context_data = asyncio.run(
            api.multi_index_global_search(
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
                callbacks=callbacks
            )
        )
        logger.success(f"Global Search Response:\n{response}")
        # NOTE: we return the response and context data here purely as a complete demonstration of the API.
        # External users should use the API directly to get the response and context data.
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

            global_callbacks = callbacks + [NoopQueryCallbacks()]  # Combine with existing callbacks
            global_callbacks[-1].on_context = on_context

            async for stream_chunk in api.global_search_streaming(
                config=config,
                entities=final_entities,
                communities=final_communities,
                community_reports=final_community_reports,
                community_level=community_level,
                dynamic_community_selection=dynamic_community_selection,
                response_type=response_type,
                query=query,
                callbacks=global_callbacks,  # Use combined callbacks
            ):
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
            entities=final_entities,
            communities=final_communities,
            community_reports=final_community_reports,
            community_level=community_level,
            dynamic_community_selection=dynamic_community_selection,
            response_type=response_type,
            query=query,
            callbacks=callbacks  
        )
    )
    logger.success(f"Global Search Response:\n{response}")
    # NOTE: we return the response and context data here purely as a complete demonstration of the API.
    # External users should use the API directly to get the response and context data.
    return response, context_data




def run_local_search(
    config_filepath: Path | None,
    data_dir: Path | None,
    root_dir: Path,
    community_level: int,
    response_type: str,
    streaming: bool,
    query: str,
    raw_chunks: bool = False,
):
    """Perform a local search with a given query.

    Loads index files required for local search and calls the Query API.
    """
    # Add debug print at start of function
    print(f"\nDEBUG: run_local_search called with raw_chunks={raw_chunks}")
    
    root = root_dir.resolve()
    cli_overrides = {}
    if data_dir:
        cli_overrides["output.base_dir"] = str(data_dir)
    config = load_config(root, config_filepath, cli_overrides)
    
    # Initialize callbacks list
    callbacks = []
    if raw_chunks:
        callbacks.append(RawChunksCallback())
    
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

        logger.success(
            f"Running Multi-index Local Search: {dataframe_dict['index_names']}"
        )

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
                callbacks=callbacks,
            )
        )
        logger.success(f"Local Search Response:\n{response}")
        # NOTE: we return the response and context data here purely as a complete demonstration of the API.
        # External users should use the API directly to get the response and context data.
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

            local_callbacks = callbacks + [NoopQueryCallbacks()]
            local_callbacks[-1].on_context = on_context

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
                callbacks=local_callbacks,
            ):
                full_response += stream_chunk
                print(stream_chunk, end="")
                sys.stdout.flush()
            print()
            return full_response, context_data

        return asyncio.run(run_streaming_search())
    else:
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
                callbacks=callbacks,
            )
        )
    logger.success(f"Local Search Response:\n{response}")
    # NOTE: we return the response and context data here purely as a complete demonstration of the API.
    # External users should use the API directly to get the response and context data.
    return response, context_data


def run_drift_search(
    config_filepath: Path | None,
    data_dir: Path | None,
    root_dir: Path,
    community_level: int,
    response_type: str,
    streaming: bool,
    query: str,
    raw_chunks: bool = False  # Added raw_chunks parameter
):
    """Perform a local search with a given query.

    Loads index files required for local search and calls the Query API.
    """
    print(f"\nDEBUG: run_drift_search called with raw_chunks={raw_chunks}")
    
    root = root_dir.resolve()
    cli_overrides = {}
    if data_dir:
        cli_overrides["output.base_dir"] = str(data_dir)
    config = load_config(root, config_filepath, cli_overrides)
    
    # Initialize callbacks list
    callbacks = []
    if raw_chunks:
        callbacks.append(RawChunksCallback())

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

        logger.success(
            f"Running Multi-index Drift Search: {dataframe_dict['index_names']}"
        )

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
                callbacks=callbacks  # Added callbacks parameter
            )
        )
        logger.success(f"DRIFT Search Response:\n{response}")
        # NOTE: we return the response and context data here purely as a complete demonstration of the API.
        # External users should use the API directly to get the response and context data.
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

            drift_callbacks = callbacks + [NoopQueryCallbacks()]  # Combine with existing callbacks
            drift_callbacks[-1].on_context = on_context


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
                callbacks=drift_callbacks,  # Use combined callbacks
            ):
                full_response += stream_chunk
                print(stream_chunk, end="")  # noqa: T201
                sys.stdout.flush()  # flush output buffer to display text immediately
            print()  # noqa: T201
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
            callbacks=callbacks  # Added callbacks parameter
        )
    )
    logger.success(f"DRIFT Search Response:\n{response}")
    # NOTE: we return the response and context data here purely as a complete demonstration of the API.
    # External users should use the API directly to get the response and context data.
    return response, context_data


def run_basic_search(
    config_filepath: Path | None,
    data_dir: Path | None,
    root_dir: Path,
    streaming: bool,
    query: str,
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

        logger.success(
            f"Running Multi-index Basic Search: {dataframe_dict['index_names']}"
        )

        response, context_data = asyncio.run(
            api.multi_index_basic_search(
                config=config,
                text_units_list=final_text_units_list,
                index_names=index_names,
                streaming=streaming,
                query=query,
            )
        )
        logger.success(f"Basic Search Response:\n{response}")
        # NOTE: we return the response and context data here purely as a complete demonstration of the API.
        # External users should use the API directly to get the response and context data.
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
            ):
                full_response += stream_chunk
                print(stream_chunk, end="")  # noqa: T201
                sys.stdout.flush()  # flush output buffer to display text immediately
            print()  # noqa: T201
            return full_response, context_data

        return asyncio.run(run_streaming_search())
    # not streaming
    response, context_data = asyncio.run(
        api.basic_search(
            config=config,
            text_units=final_text_units,
            query=query,
        )
    )
    logger.success(f"Basic Search Response:\n{response}")
    # NOTE: we return the response and context data here purely as a complete demonstration of the API.
    # External users should use the API directly to get the response and context data.
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
