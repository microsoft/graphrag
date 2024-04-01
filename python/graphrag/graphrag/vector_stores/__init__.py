#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""A package containing vector-storage implementations."""
from .base import BaseVectorStore, VectorStoreDocument, VectorStoreSearchResult

__all__ = ["BaseVectorStore", "VectorStoreDocument", "VectorStoreSearchResult"]
