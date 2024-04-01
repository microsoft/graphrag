#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""The Indexing Engine graph embedding package root."""
from .embedding import NodeEmbeddings, embed_nod2vec

__all__ = ["NodeEmbeddings", "embed_nod2vec"]
