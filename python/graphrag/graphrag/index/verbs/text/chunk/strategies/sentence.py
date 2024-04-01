#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""A module containing run method definition."""
from collections.abc import Iterable
from typing import Any

import nltk
from datashaper import ProgressTicker

from .typing import TextChunk


def run(
    input: list[str], _args: dict[str, Any], tick: ProgressTicker
) -> Iterable[TextChunk]:
    """Chunks text into multiple parts. A pipeline verb."""
    for doc_idx, text in enumerate(input):
        sentences = nltk.sent_tokenize(text)
        for sentence in sentences:
            yield TextChunk(
                text_chunk=sentence,
                source_doc_indices=[doc_idx],
            )
        tick(1)
