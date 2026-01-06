# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'create_chunk_results' function."""

from collections.abc import Callable

from graphrag_chunking.chunk_result import ChunkResult


def create_chunk_results(
    chunks: list[str],
    encode: Callable[[str], list[int]] | None = None,
) -> list[ChunkResult]:
    """Create chunk results from a list of text chunks. The index assignments are 0-based and assume chunks we not stripped relative to the source text."""
    results = []
    start_char = 0
    for index, chunk in enumerate(chunks):
        end_char = start_char + len(chunk) - 1  # 0-based indices
        chunk = ChunkResult(
            text=chunk,
            index=index,
            start_char=start_char,
            end_char=end_char,
        )
        if encode:
            chunk.token_count = len(encode(chunk.text))
        results.append(chunk)
        start_char = end_char + 1
    return results
