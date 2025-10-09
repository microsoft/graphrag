# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'GraphExtractionResult' and 'GraphExtractor' models."""

import logging
import re
import traceback
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import networkx as nx

from graphrag.index.typing.error_handler import ErrorHandlerFn
from graphrag.index.utils.string import clean_str
from graphrag.language_model.protocol.base import ChatModel
from graphrag.prompts.index.extract_graph import (
    CONTINUE_PROMPT,
    LOOP_PROMPT,
)

INPUT_TEXT_KEY = "input_text"
RECORD_DELIMITER_KEY = "record_delimiter"
COMPLETION_DELIMITER_KEY = "completion_delimiter"
ENTITY_TYPES_KEY = "entity_types"
TUPLE_DELIMITER = "<|>"
RECORD_DELIMITER = "##"
COMPLETION_DELIMITER = "<|COMPLETE|>"
DEFAULT_ENTITY_TYPES = ["organization", "person", "geo", "event"]

logger = logging.getLogger(__name__)


@dataclass
class GraphExtractionResult:
    """Unipartite graph extraction result class definition."""

    output: nx.Graph
    source_docs: dict[Any, Any]


class GraphExtractor:
    """Unipartite graph extractor class definition."""

    _model: ChatModel
    _join_descriptions: bool
    _extraction_prompt: str
    _max_gleanings: int
    _on_error: ErrorHandlerFn

    def __init__(
        self,
        model: ChatModel,
        prompt: str,
        max_gleanings: int,
        join_descriptions=True,
        on_error: ErrorHandlerFn | None = None,
    ):
        """Init method definition."""
        self._model = model
        self._join_descriptions = join_descriptions
        self._extraction_prompt = prompt
        self._max_gleanings = max_gleanings
        self._on_error = on_error or (lambda _e, _s, _d: None)

    async def __call__(
        self, texts: list[str], entity_types: list[str]
    ) -> GraphExtractionResult:
        """Call method definition."""
        all_records: dict[int, str] = {}
        source_doc_map: dict[int, str] = {}

        for doc_index, text in enumerate(texts):
            try:
                # Invoke the entity extraction
                result = await self._process_document(text, entity_types)
                source_doc_map[doc_index] = text
                all_records[doc_index] = result
            except Exception as e:
                logger.exception("error extracting graph")
                self._on_error(
                    e,
                    traceback.format_exc(),
                    {
                        "doc_index": doc_index,
                        "text": text,
                    },
                )

        output = await self._process_results(
            all_records,
            TUPLE_DELIMITER,
            RECORD_DELIMITER,
        )

        return GraphExtractionResult(
            output=output,
            source_docs=source_doc_map,
        )

    async def _process_document(self, text: str, entity_types: list[str]) -> str:
        response = await self._model.achat(
            self._extraction_prompt.format(**{
                INPUT_TEXT_KEY: text,
                ENTITY_TYPES_KEY: ",".join(entity_types),
            }),
        )
        results = response.output.content or ""

        # if gleanings are specified, enter a loop to extract more entities
        # there are two exit criteria: (a) we hit the configured max, (b) the model says there are no more entities
        if self._max_gleanings > 0:
            for i in range(self._max_gleanings):
                response = await self._model.achat(
                    CONTINUE_PROMPT,
                    name=f"extract-continuation-{i}",
                    history=response.history,
                )
                results += response.output.content or ""

                # if this is the final glean, don't bother updating the continuation flag
                if i >= self._max_gleanings - 1:
                    break

                response = await self._model.achat(
                    LOOP_PROMPT,
                    name=f"extract-loopcheck-{i}",
                    history=response.history,
                )
                if response.output.content != "Y":
                    break

        return results

    async def _process_results(
        self,
        results: dict[int, str],
        tuple_delimiter: str,
        record_delimiter: str,
    ) -> nx.Graph:
        """Parse the result string to create an undirected unipartite graph.

        Args:
            - results - dict of results from the extraction chain
            - tuple_delimiter - delimiter between tuples in an output record, default is '<|>'
            - record_delimiter - delimiter between records, default is '##'
        Returns:
            - output - unipartite graph in graphML format
        """
        graph = nx.Graph()
        for source_doc_id, extracted_data in results.items():
            records = [r.strip() for r in extracted_data.split(record_delimiter)]

            for record in records:
                record = re.sub(r"^\(|\)$", "", record.strip())
                record_attributes = record.split(tuple_delimiter)

                if record_attributes[0] == '"entity"' and len(record_attributes) >= 4:
                    # add this record as a node in the G
                    entity_name = clean_str(record_attributes[1].upper())
                    entity_type = clean_str(record_attributes[2].upper())
                    entity_description = clean_str(record_attributes[3])

                    if entity_name in graph.nodes():
                        node = graph.nodes[entity_name]
                        if self._join_descriptions:
                            node["description"] = "\n".join(
                                list({
                                    *_unpack_descriptions(node),
                                    entity_description,
                                })
                            )
                        else:
                            if len(entity_description) > len(node["description"]):
                                node["description"] = entity_description
                        node["source_id"] = ", ".join(
                            list({
                                *_unpack_source_ids(node),
                                str(source_doc_id),
                            })
                        )
                        node["type"] = (
                            entity_type if entity_type != "" else node["type"]
                        )
                    else:
                        graph.add_node(
                            entity_name,
                            type=entity_type,
                            description=entity_description,
                            source_id=str(source_doc_id),
                        )

                if (
                    record_attributes[0] == '"relationship"'
                    and len(record_attributes) >= 5
                ):
                    # add this record as edge
                    source = clean_str(record_attributes[1].upper())
                    target = clean_str(record_attributes[2].upper())
                    edge_description = clean_str(record_attributes[3])
                    edge_source_id = clean_str(str(source_doc_id))
                    try:
                        weight = float(record_attributes[-1])
                    except ValueError:
                        weight = 1.0

                    if source not in graph.nodes():
                        graph.add_node(
                            source,
                            type="",
                            description="",
                            source_id=edge_source_id,
                        )
                    if target not in graph.nodes():
                        graph.add_node(
                            target,
                            type="",
                            description="",
                            source_id=edge_source_id,
                        )
                    if graph.has_edge(source, target):
                        edge_data = graph.get_edge_data(source, target)
                        if edge_data is not None:
                            weight += edge_data["weight"]
                            if self._join_descriptions:
                                edge_description = "\n".join(
                                    list({
                                        *_unpack_descriptions(edge_data),
                                        edge_description,
                                    })
                                )
                            edge_source_id = ", ".join(
                                list({
                                    *_unpack_source_ids(edge_data),
                                    str(source_doc_id),
                                })
                            )
                    graph.add_edge(
                        source,
                        target,
                        weight=weight,
                        description=edge_description,
                        source_id=edge_source_id,
                    )

        return graph


def _unpack_descriptions(data: Mapping) -> list[str]:
    value = data.get("description", None)
    return [] if value is None else value.split("\n")


def _unpack_source_ids(data: Mapping) -> list[str]:
    value = data.get("source_id", None)
    return [] if value is None else value.split(", ")
