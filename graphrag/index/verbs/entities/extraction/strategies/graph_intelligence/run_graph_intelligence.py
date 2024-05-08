# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_gi,  run_extract_entities and _create_text_splitter methods to run graph intelligence."""

import networkx as nx
from datashaper import VerbCallbacks

from graphrag.config.enums import LLMType
from graphrag.index.cache import PipelineCache
from graphrag.index.graph.extractors.graph import GraphExtractor
from graphrag.index.llm import load_llm
from graphrag.index.text_splitting import (
    NoopTextSplitter,
    TextSplitter,
    TokenTextSplitter,
)
from graphrag.index.verbs.entities.extraction.strategies.typing import (
    Document,
    EntityExtractionResult,
    EntityTypes,
    StrategyConfig,
)
from graphrag.llm import CompletionLLM

from .defaults import DEFAULT_LLM_CONFIG


async def run_gi(
    docs: list[Document],
    entity_types: EntityTypes,
    reporter: VerbCallbacks,
    pipeline_cache: PipelineCache,
    args: StrategyConfig,
) -> EntityExtractionResult:
    """Run the graph intelligence entity extraction strategy."""
    llm_config = args.get("llm", DEFAULT_LLM_CONFIG)
    llm_type = llm_config.get("type", LLMType.StaticResponse)
    llm = load_llm("entity_extraction", llm_type, reporter, pipeline_cache, llm_config)
    return await run_extract_entities(llm, docs, entity_types, reporter, args)


async def run_extract_entities(
    llm: CompletionLLM,
    docs: list[Document],
    entity_types: EntityTypes,
    reporter: VerbCallbacks | None,
    args: StrategyConfig,
) -> EntityExtractionResult:
    """Run the entity extraction chain."""
    encoding_name = args.get("encoding_name", "cl100k_base")

    # Chunking Arguments
    prechunked = args.get("prechunked", False)
    chunk_size = args.get("chunk_size", 2500)
    chunk_overlap = args.get("chunk_overlap", 300)

    # Extraction Arguments
    tuple_delimiter = args.get("tuple_delimiter", None)
    record_delimiter = args.get("record_delimiter", None)
    completion_delimiter = args.get("completion_delimiter", None)
    extraction_prompt = args.get("extraction_prompt", None)
    encoding_model = args.get("encoding_name", None)
    max_gleanings = args.get("max_gleanings", None)

    # note: We're not using UnipartiteGraphChain.from_params
    # because we want to pass "timeout" to the llm_kwargs
    text_splitter = _create_text_splitter(
        prechunked, chunk_size, chunk_overlap, encoding_name
    )

    extractor = GraphExtractor(
        llm_invoker=llm,
        prompt=extraction_prompt,
        encoding_model=encoding_model,
        max_gleanings=max_gleanings,
        on_error=lambda e, s, d: (
            reporter.error("Entity Extraction Error", e, s, d) if reporter else None
        ),
    )
    text_list = [doc.text.strip() for doc in docs]

    # If it's not pre-chunked, then re-chunk the input
    if not prechunked:
        text_list = text_splitter.split_text("\n".join(text_list))

    results = await extractor(
        list(text_list),
        {
            "entity_types": entity_types,
            "tuple_delimiter": tuple_delimiter,
            "record_delimiter": record_delimiter,
            "completion_delimiter": completion_delimiter,
        },
    )

    graph = results.output
    # Map the "source_id" back to the "id" field
    for _, node in graph.nodes(data=True):  # type: ignore
        if node is not None:
            node["source_id"] = ",".join(
                docs[int(id)].id for id in node["source_id"].split(",")
            )

    for _, _, edge in graph.edges(data=True):  # type: ignore
        if edge is not None:
            edge["source_id"] = ",".join(
                docs[int(id)].id for id in edge["source_id"].split(",")
            )

    entities = [
        ({"name": item[0], **(item[1] or {})})
        for item in graph.nodes(data=True)
        if item is not None
    ]

    graph_data = "".join(nx.generate_graphml(graph))
    return EntityExtractionResult(entities, graph_data)


def _create_text_splitter(
    prechunked: bool, chunk_size: int, chunk_overlap: int, encoding_name: str
) -> TextSplitter:
    """Create a text splitter for the extraction chain.

    Args:
        - prechunked - Whether the text is already chunked
        - chunk_size - The size of each chunk
        - chunk_overlap - The overlap between chunks
        - encoding_name - The name of the encoding to use
    Returns:
        - output - A text splitter
    """
    if prechunked:
        return NoopTextSplitter()

    return TokenTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        encoding_name=encoding_name,
    )
