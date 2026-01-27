# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Basic Context Builder implementation."""

import logging
from typing import TYPE_CHECKING, cast

import pandas as pd
from graphrag_llm.tokenizer import Tokenizer
from graphrag_vectors import VectorStore

from graphrag.data_model.text_unit import TextUnit
from graphrag.query.context_builder.builders import (
    BasicContextBuilder,
    ContextBuilderResult,
)
from graphrag.query.context_builder.conversation_history import ConversationHistory
from graphrag.tokenizer.get_tokenizer import get_tokenizer

if TYPE_CHECKING:
    from graphrag_llm.embedding import LLMEmbedding

logger = logging.getLogger(__name__)


class BasicSearchContext(BasicContextBuilder):
    """Class representing the Basic Search Context Builder."""

    def __init__(
        self,
        text_embedder: "LLMEmbedding",
        text_unit_embeddings: VectorStore,
        text_units: list[TextUnit] | None = None,
        tokenizer: Tokenizer | None = None,
        embedding_vectorstore_key: str = "id",
    ):
        self.text_embedder = text_embedder
        self.tokenizer = tokenizer or get_tokenizer()
        self.text_units = text_units
        self.text_unit_embeddings = text_unit_embeddings
        self.embedding_vectorstore_key = embedding_vectorstore_key

    def build_context(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        k: int = 10,
        max_context_tokens: int = 12_000,
        context_name: str = "Sources",
        column_delimiter: str = "|",
        text_id_col: str = "id",
        text_col: str = "text",
        **kwargs,
    ) -> ContextBuilderResult:
        """Build the context for the basic search mode."""
        if query != "":
            related_texts = self.text_unit_embeddings.similarity_search_by_text(
                text=query,
                text_embedder=lambda t: (
                    self.text_embedder.embedding(input=[t]).first_embedding
                ),
                k=k,
            )

            text_unit_ids = {t.document.id for t in related_texts}
            text_units_filtered = []
            text_units_filtered = [
                {text_id_col: t.short_id, text_col: t.text}
                for t in self.text_units or []
                if t.id in text_unit_ids
            ]
            related_text_df = pd.DataFrame(text_units_filtered)
        else:
            related_text_df = pd.DataFrame({
                text_id_col: [],
                text_col: [],
            })

        # add these related text chunks into context until we fill up the context window
        current_tokens = 0
        text_ids = []
        current_tokens = len(
            self.tokenizer.encode(text_id_col + column_delimiter + text_col + "\n")
        )
        for i, row in related_text_df.iterrows():
            text = row[text_id_col] + column_delimiter + row[text_col] + "\n"
            tokens = len(self.tokenizer.encode(text))
            if current_tokens + tokens > max_context_tokens:
                msg = f"Reached token limit: {current_tokens + tokens}. Reverting to previous context state"
                logger.warning(msg)
                break

            current_tokens += tokens
            text_ids.append(i)
        final_text_df = cast(
            "pd.DataFrame",
            related_text_df[related_text_df.index.isin(text_ids)].reset_index(
                drop=True
            ),
        )
        final_text = final_text_df.to_csv(
            index=False, escapechar="\\", sep=column_delimiter
        )

        return ContextBuilderResult(
            context_chunks=final_text,
            context_records={context_name.lower(): final_text_df},
        )
