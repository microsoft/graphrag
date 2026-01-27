# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing 'create_chunk_results' function."""

from collections.abc import Callable

from graphrag_chunking.text_chunk import TextChunk


def create_chunk_results(
    chunks: list[str],
    transform: Callable[[str], str] | None = None,
    encode: Callable[[str], list[int]] | None = None,
) -> list[TextChunk]:
    """Create chunk results from a list of text chunks. The index assignments are 0-based and assume chunks were not stripped relative to the source text."""
    results = []
    start_char = 0
    for index, chunk in enumerate(chunks):
        end_char = start_char + len(chunk) - 1  # 0-based indices
        result = TextChunk(
            original=chunk,
            text=transform(chunk) if transform else chunk,
            index=index,
            start_char=start_char,
            end_char=end_char,
        )
        if encode:
            result.token_count = len(encode(result.text))
        results.append(result)
        start_char = end_char + 1
    return results
