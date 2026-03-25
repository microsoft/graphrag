# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing run_workflow method definition."""

import logging
import re
from typing import Any

from graphrag_chunking.chunker import Chunker
from graphrag_chunking.chunker_factory import create_chunker
from graphrag_chunking.text_chunk import TextChunk
from graphrag_chunking.transformers import add_metadata
from graphrag_input import TextDocument
from graphrag_llm.tokenizer import Tokenizer
from graphrag_storage.tables.table import Table

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.typing.context import PipelineRunContext
from graphrag.index.typing.workflow import WorkflowFunctionOutput
from graphrag.index.utils.hashing import gen_sha512_hash
from graphrag.index.utils.temporal_trace import trace_event
from graphrag.logger.progress import progress_ticker
from graphrag.tokenizer.get_tokenizer import get_tokenizer

logger = logging.getLogger(__name__)
_TURN_MARKER_PATTERN = re.compile(r"(?im)^(user|assistant)\s*:\s*")


async def run_workflow(
    config: GraphRagConfig,
    context: PipelineRunContext,
) -> WorkflowFunctionOutput:
    """All the steps to transform base text_units."""
    logger.info("Workflow started: create_base_text_units")

    tokenizer = get_tokenizer(encoding_model=config.chunking.encoding_model)
    chunker = create_chunker(config.chunking, tokenizer.encode, tokenizer.decode)

    async with (
        context.output_table_provider.open("documents") as documents_table,
        context.output_table_provider.open("text_units") as text_units_table,
    ):
        total_rows = await documents_table.length()
        sample_rows = await create_base_text_units(
            documents_table,
            text_units_table,
            total_rows,
            context.callbacks,
            tokenizer=tokenizer,
            chunker=chunker,
            prepend_metadata=config.chunking.prepend_metadata,
        )

    logger.info("Workflow completed: create_base_text_units")
    return WorkflowFunctionOutput(result=sample_rows)


async def create_base_text_units(
    documents_table: Table,
    text_units_table: Table,
    total_rows: int,
    callbacks: WorkflowCallbacks,
    tokenizer: Tokenizer,
    chunker: Chunker,
    prepend_metadata: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Transform documents into chunked text units via streaming read/write.

    Reads documents row-by-row from an async iterable and writes text units
    directly to the output table, avoiding loading all data into memory.

    Args
    ----
        documents_table: Table
            Table instance for reading documents. Supports async iteration.
        text_units_table: Table
            Table instance for writing text units row by row.
        total_rows: int
            Total number of documents for progress reporting.
        callbacks: WorkflowCallbacks
            Callbacks for progress reporting.
        tokenizer: Tokenizer
            Tokenizer for measuring chunk token counts.
        chunker: Chunker
            Chunker instance for splitting document text.
        prepend_metadata: list[str] | None
            Optional list of metadata fields to prepend to
            each chunk.
    """
    tick = progress_ticker(callbacks.progress, total_rows)

    logger.info(
        "Starting chunking process for %d documents",
        total_rows,
    )

    doc_index = 0
    sample_rows: list[dict[str, Any]] = []
    sample_size = 5
    chunk_index_in_conversation: dict[str, int] = {}
    emitted_chunks = 0

    async for doc in documents_table:
        chunks = chunk_document(doc, chunker, prepend_metadata)
        turn_spans = _infer_turn_spans(doc)
        conversation_id = str(doc.get("conversation_id") or "__missing_conversation_id__")
        trace_event(
            logger,
            stage="chunking",
            event="document_chunking_start",
            doc_id=doc.get("id"),
            conversation_id=doc.get("conversation_id"),
            row_turn_index=doc.get("turn_index"),
            row_turn_timestamp=doc.get("turn_timestamp"),
            row_turn_role=doc.get("turn_role"),
            chunk_count=len(chunks),
        )
        for chunk in chunks:
            if chunk.text is None:
                continue
            temporal = _chunk_temporal_metadata(doc, turn_spans, chunk)
            current_chunk_index = chunk_index_in_conversation.get(conversation_id, 0)
            chunk_index_in_conversation[conversation_id] = current_chunk_index + 1
            row = {
                "id": "",
                "document_id": doc["id"],
                "text": chunk.text,
                "n_tokens": len(tokenizer.encode(chunk.text)),
                "conversation_id": doc.get("conversation_id"),
                "turn_index": doc.get("turn_index"),
                "turn_timestamp": doc.get("turn_timestamp"),
                "turn_role": doc.get("turn_role"),
                "start_turn_index": temporal["start_turn_index"],
                "end_turn_index": temporal["end_turn_index"],
                "turn_timestamp_start": temporal["turn_timestamp_start"],
                "turn_timestamp_end": temporal["turn_timestamp_end"],
                "included_roles": temporal["included_roles"],
                "chunk_index_in_document": chunk.index,
                "chunk_index_in_conversation": current_chunk_index,
            }
            row["id"] = gen_sha512_hash(row, ["text"])
            await text_units_table.write(row)
            emitted_chunks += 1
            trace_event(
                logger,
                stage="chunking",
                event="text_unit_emitted",
                text_unit_id=row["id"],
                doc_id=row["document_id"],
                conversation_id=row.get("conversation_id"),
                chunk_index_in_document=row["chunk_index_in_document"],
                chunk_index_in_conversation=row["chunk_index_in_conversation"],
                start_turn_index=row["start_turn_index"],
                end_turn_index=row["end_turn_index"],
                turn_timestamp_start=row["turn_timestamp_start"],
                turn_timestamp_end=row["turn_timestamp_end"],
                included_roles=row["included_roles"],
                preview_fields={"chunk_text": row.get("text", "")},
            )

            if len(sample_rows) < sample_size:
                sample_rows.append(row)

        doc_index += 1
        tick()
        logger.info(
            "chunker progress:  %d/%d",
            doc_index,
            total_rows,
        )

    trace_event(
        logger,
        stage="chunking",
        event="chunking_complete",
        total_documents=doc_index,
        emitted_text_units=emitted_chunks,
    )
    return sample_rows


def chunk_document(
    doc: dict[str, Any],
    chunker: Chunker,
    prepend_metadata: list[str] | None = None,
) -> list[TextChunk]:
    """Chunk a single document row into text fragments.

    Args
    ----
        doc: dict[str, Any]
            A single document row as a dictionary.
        chunker: Chunker
            Chunker instance for splitting text.
        prepend_metadata: list[str] | None
            Optional metadata fields to prepend.

    Returns
    -------
        list[TextChunk]:
            List of chunk objects.
    """
    transformer = None
    if prepend_metadata:
        document = TextDocument(
            id=doc["id"],
            title=doc.get("title", ""),
            text=doc["text"],
            creation_date=doc.get("creation_date", ""),
            raw_data=doc.get("raw_data"),
        )
        metadata = document.collect(prepend_metadata)
        transformer = add_metadata(metadata=metadata, line_delimiter=".\n")

    return chunker.chunk(doc["text"], transform=transformer)


def _infer_turn_spans(doc: dict[str, Any]) -> list[dict[str, Any]]:
    text = str(doc.get("text") or "")
    # 정책: JSON 입력은 "row 1개 = turn 1개"로 본다.
    # 따라서 한 row 내부 텍스트는 여러 turn으로 분해하지 않고 단일 span으로 유지한다.
    # (라벨이 없어도 일반적인 케이스로 처리)
    single = _single_span(doc, len(text))

    # role이 비어 있으면 텍스트 접두 라벨(user:/assistant:/system:)만 가볍게 추론한다.
    if single["turn_role"] == "unknown":
        inferred_role = _infer_role_from_text(text)
        if inferred_role != "unknown":
            single["turn_role"] = inferred_role

    return [single]


def _single_span(doc: dict[str, Any], text_length: int) -> dict[str, Any]:
    return {
        "start_char": 0,
        "end_char": text_length,
        "turn_index": _safe_int(doc.get("turn_index"), 0),
        "turn_timestamp": doc.get("turn_timestamp"),
        "turn_role": str(doc.get("turn_role") or "unknown"),
    }


def _normalize_role(label: str) -> str:
    normalized = label.strip().lower()
    if normalized in {"user", "assistant", "system"}:
        return normalized
    return "unknown"


def _infer_role_from_text(text: str) -> str:
    match = _TURN_MARKER_PATTERN.search(text)
    if not match:
        return "unknown"
    return _normalize_role(match.group(1))


def _chunk_temporal_metadata(
    doc: dict[str, Any],
    turn_spans: list[dict[str, Any]],
    chunk: TextChunk,
) -> dict[str, Any]:
    overlapping = [
        span
        for span in turn_spans
        if span["start_char"] < chunk.end_char and span["end_char"] > chunk.start_char
    ]
    if not overlapping:
        default_turn = _safe_int(doc.get("turn_index"), 0)
        default_ts = doc.get("turn_timestamp")
        default_role = _normalize_role(str(doc.get("turn_role") or "unknown"))
        return {
            "start_turn_index": default_turn,
            "end_turn_index": default_turn,
            "turn_timestamp_start": default_ts,
            "turn_timestamp_end": default_ts,
            "included_roles": [default_role],
        }

    ordered_overlapping = sorted(
        overlapping,
        key=lambda span: (_safe_int(span.get("turn_index"), 0), span.get("start_char", 0)),
    )
    roles = sorted(
        {
            _normalize_role(str(span.get("turn_role") or "unknown"))
            for span in ordered_overlapping
        }
    )
    start_turn_index = _safe_int(ordered_overlapping[0].get("turn_index"), 0)
    end_turn_index = _safe_int(ordered_overlapping[-1].get("turn_index"), 0)
    timestamps = [
        span.get("turn_timestamp")
        for span in ordered_overlapping
        if span.get("turn_timestamp")
    ]
    turn_timestamp_start = timestamps[0] if timestamps else doc.get("turn_timestamp")
    turn_timestamp_end = timestamps[-1] if timestamps else doc.get("turn_timestamp")
    return {
        "start_turn_index": start_turn_index,
        "end_turn_index": end_turn_index,
        "turn_timestamp_start": turn_timestamp_start,
        "turn_timestamp_end": turn_timestamp_end,
        "included_roles": roles,
    }


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
