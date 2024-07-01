# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run method definition."""

import networkx as nx
import nltk
from datashaper import VerbCallbacks
from nltk.corpus import words

from graphrag.index.cache import PipelineCache

from .typing import Document, EntityExtractionResult, EntityTypes, StrategyConfig

# Need to do this cause we're potentially multithreading, and nltk doesn't like that
words.ensure_loaded()


async def run(  # noqa RUF029 async is required for interface
    docs: list[Document],
    entity_types: EntityTypes,
    reporter: VerbCallbacks,  # noqa ARG001
    pipeline_cache: PipelineCache,  # noqa ARG001
    args: StrategyConfig,  # noqa ARG001
) -> EntityExtractionResult:
    """Run method definition."""
    entity_map = {}
    graph = nx.Graph()
    for doc in docs:
        connected_entities = []
        for chunk in nltk.ne_chunk(nltk.pos_tag(nltk.word_tokenize(doc.text))):
            if hasattr(chunk, "label"):
                entity_type = chunk.label().lower()
                if entity_type in entity_types:
                    name = (" ".join(c[0] for c in chunk)).upper()
                    connected_entities.append(name)
                    if name not in entity_map:
                        entity_map[name] = entity_type
                        graph.add_node(
                            name, type=entity_type, description=name, source_id=doc.id
                        )

        # connect the entities if they appear in the same document
        if len(connected_entities) > 1:
            for i in range(len(connected_entities)):
                for j in range(i + 1, len(connected_entities)):
                    description = f"{connected_entities[i]} -> {connected_entities[j]}"
                    graph.add_edge(
                        connected_entities[i],
                        connected_entities[j],
                        description=description,
                        source_id=doc.id,
                    )

    return EntityExtractionResult(
        entities=[
            {"type": entity_type, "name": name}
            for name, entity_type in entity_map.items()
        ],
        graphml_graph="".join(nx.generate_graphml(graph)),
    )
