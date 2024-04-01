#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""Token limit method definition."""
from .text_splitting import TokenTextSplitter


def check_token_limit(text, max_token):
    """Check token limit."""
    text_splitter = TokenTextSplitter(chunk_size=max_token, chunk_overlap=0)
    docs = text_splitter.split_text(text)
    if len(docs) > 1:
        return 0
    return 1
