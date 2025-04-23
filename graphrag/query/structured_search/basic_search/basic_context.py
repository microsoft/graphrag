# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Basic Context Builder implementation."""

import logging
from typing import cast

import pandas as pd
import tiktoken

from graphrag.data_model.text_unit import TextUnit
from graphrag.language_model.protocol.base import EmbeddingModel
from graphrag.query.context_builder.builders import (
    BasicContextBuilder,
    ContextBuilderResult,
)
from graphrag.query.context_builder.conversation_history import ConversationHistory
from graphrag.query.llm.text_utils import num_tokens
from graphrag.vector_stores.base import BaseVectorStore

log = logging.getLogger(__name__)


class BasicSearchContext(BasicContextBuilder):
    """Class representing the Basic Search Context Builder."""

    def __init__(
        self,
        text_embedder: EmbeddingModel,
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
        self.text_id_map = self._map_ids()

    def build_context(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        k: int = 10,
        max_context_tokens: int = 12_000,
        context_name: str = "Sources",
        column_delimiter: str = "|",
        text_id_col: str = "source_id",
        text_col: str = "text",
        **kwargs,
    ) -> ContextBuilderResult:
        """Build the context for the basic search mode."""
        if query != "":
            related_texts = self.text_unit_embeddings.similarity_search_by_text(
                text=query,
                text_embedder=lambda t: self.text_embedder.embed(t),
                k=k,
            )
            related_text_list = [
                {
                    text_id_col: self.text_id_map[f"{chunk.document.id}"],
                    text_col: chunk.document.text,
                }
                for chunk in related_texts
            ]
            related_text_df = pd.DataFrame(related_text_list)
        else:
            related_text_df = pd.DataFrame({
                text_id_col: [],
                text_col: [],
            })

        # add these related text chunks into context until we fill up the context window
        current_tokens = 0
        text_ids = []
        current_tokens = num_tokens(
            text_id_col + column_delimiter + text_col + "\n", self.token_encoder
        )
        for i, row in related_text_df.iterrows():
            text = row[text_id_col] + column_delimiter + row[text_col] + "\n"
            tokens = num_tokens(text, self.token_encoder)
            if current_tokens + tokens > max_context_tokens:
                msg = f"Reached token limit: {current_tokens + tokens}. Reverting to previous context state"
                log.info(msg)
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
            context_records={context_name: final_text_df},
        )

    def _map_ids(self) -> dict[str, str]:
        """Map id to short id in the text units."""
        id_map = {}
        text_units = self.text_units or []
        for unit in text_units:
            id_map[unit.id] = unit.short_id
        return id_map
