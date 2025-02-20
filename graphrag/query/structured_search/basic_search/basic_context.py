# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Basic Context Builder implementation."""

import pandas as pd
import tiktoken

from graphrag.data_model.text_unit import TextUnit
from graphrag.query.context_builder.builders import (
    BasicContextBuilder,
    ContextBuilderResult,
)
from graphrag.query.context_builder.conversation_history import ConversationHistory
from graphrag.query.llm.base import BaseTextEmbedding
from graphrag.vector_stores.base import BaseVectorStore


class BasicSearchContext(BasicContextBuilder):
    """Class representing the Basic Search Context Builder."""

    def __init__(
        self,
        text_embedder: BaseTextEmbedding,
        text_unit_embeddings: BaseVectorStore,
        text_units: list[TextUnit] | None = None,
        token_encoder: tiktoken.Encoding | None = None,
        embedding_vectorstore_key: str = "id",
    ):
        self.text_embedder = text_embedder
        self.token_encoder = token_encoder
        self.text_units = text_units
        self.text_unit_embeddings = text_unit_embeddings
        self.embedding_vectorstore_key = embedding_vectorstore_key

    def build_context(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        **kwargs,
    ) -> ContextBuilderResult:
        """Build the context for the local search mode."""
        search_results = self.text_unit_embeddings.similarity_search_by_text(
            text=query,
            text_embedder=lambda t: self.text_embedder.embed(t),
            k=kwargs.get("k", 10),
        )
        # we don't have a friendly id on text_units, so just copy the index
        sources = [
            {"id": str(search_results.index(r)), "text": r.document.text}
            for r in search_results
        ]
        # make a delimited table for the context; this imitates graphrag context building
        table = ["id|text"] + [f"{s['id']}|{s['text']}" for s in sources]

        columns = pd.Index(["id", "text"])

        return ContextBuilderResult(
            context_chunks="\n\n".join(table),
            context_records={"sources": pd.DataFrame(sources, columns=columns)},
        )
