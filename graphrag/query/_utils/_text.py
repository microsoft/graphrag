# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

import typing
import itertools

import numpy as np
import tiktoken


def chunk_text(
    text: str,
    max_tokens: int,
    token_encoder: typing.Optional[tiktoken.Encoding] = None
) -> typing.Generator[str, None, None]:
    def _batched(iter_: typing.Iterator, n_: int) -> typing.Iterator:
        """
        Batch data into tuples of length n. The last batch may be shorter.

        Taken from Python's cookbook: https://docs.python.org/3/library/itertools.html#itertools.batched
        """
        # _batched('ABCDEFG', 3) --> ABC DEF G
        return iter(lambda: tuple(itertools.islice(iter_, n_)), ())

    token_encoder = tiktoken.get_encoding("cl100k_base") if token_encoder is None else token_encoder
    tokens = token_encoder.encode(text)  # type: ignore
    chunk_iterator = _batched(iter(tokens), max_tokens)
    yield from (
        token_encoder.decode(list(chunk)) for chunk in chunk_iterator
    )


def combine_embeddings(embeddings: typing.List[typing.List[float]], lengths: typing.List[int]) -> typing.List[float]:
    embeddings_ = np.average(np.array(embeddings), axis=0, weights=lengths)
    embeddings_ /= np.linalg.norm(embeddings_)  # normalize
    return embeddings_.tolist()


def num_tokens(text: str, token_encoder: typing.Optional[tiktoken.Encoding] = None) -> int:
    """Return the number of tokens in the given text."""
    token_encoder = token_encoder or tiktoken.get_encoding("cl100k_base")
    return token_encoder.encode(text).__len__()
