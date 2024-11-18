# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""DRIFT Context Builder implementation."""

import logging
from dataclasses import asdict
from typing import Any

import numpy as np
import pandas as pd
import tiktoken

from graphrag.config.models.drift_search_config import DRIFTSearchConfig
from graphrag.model.community_report import CommunityReport
from graphrag.model.covariate import Covariate
from graphrag.model.entity import Entity
from graphrag.model.relationship import Relationship
from graphrag.model.text_unit import TextUnit
from graphrag.prompts.query.drift_search_system_prompt import (
    DRIFT_LOCAL_SYSTEM_PROMPT,
)
from graphrag.query.context_builder.entity_extraction import EntityVectorStoreKey
from graphrag.query.llm.base import BaseTextEmbedding
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
from graphrag.query.structured_search.base import DRIFTContextBuilder
from graphrag.query.structured_search.drift_search.primer import PrimerQueryProcessor
from graphrag.query.structured_search.local_search.mixed_context import (
    LocalSearchMixedContext,
)
from graphrag.vector_stores.base import BaseVectorStore

log = logging.getLogger(__name__)


class DRIFTSearchContextBuilder(DRIFTContextBuilder):
    """Class representing the DRIFT Search Context Builder."""

    def __init__(
        self,
        chat_llm: ChatOpenAI,
        text_embedder: BaseTextEmbedding,
        entities: list[Entity],
        entity_text_embeddings: BaseVectorStore,
        text_units: list[TextUnit] | None = None,
        reports: list[CommunityReport] | None = None,
        relationships: list[Relationship] | None = None,
        covariates: dict[str, list[Covariate]] | None = None,
        token_encoder: tiktoken.Encoding | None = None,
        embedding_vectorstore_key: str = EntityVectorStoreKey.ID,
        config: DRIFTSearchConfig | None = None,
        local_system_prompt: str | None = None,
        local_mixed_context: LocalSearchMixedContext | None = None,
    ):
        """Initialize the DRIFT search context builder with necessary components."""
        self.config = config or DRIFTSearchConfig()
        self.chat_llm = chat_llm
        self.text_embedder = text_embedder
        self.token_encoder = token_encoder
        self.local_system_prompt = local_system_prompt or DRIFT_LOCAL_SYSTEM_PROMPT

        self.entities = entities
        self.entity_text_embeddings = entity_text_embeddings
        self.reports = reports
        self.text_units = text_units
        self.relationships = relationships
        self.covariates = covariates
        self.embedding_vectorstore_key = embedding_vectorstore_key

        self.local_mixed_context = (
            local_mixed_context or self.init_local_context_builder()
        )

    def init_local_context_builder(self) -> LocalSearchMixedContext:
        """
        Initialize the local search mixed context builder.

        Returns
        -------
        LocalSearchMixedContext: Initialized local context.
        """
        return LocalSearchMixedContext(
            community_reports=self.reports,
            text_units=self.text_units,
            entities=self.entities,
            relationships=self.relationships,
            covariates=self.covariates,
            entity_text_embeddings=self.entity_text_embeddings,
            embedding_vectorstore_key=self.embedding_vectorstore_key,
            text_embedder=self.text_embedder,
            token_encoder=self.token_encoder,
        )

    @staticmethod
    def convert_reports_to_df(reports: list[CommunityReport]) -> pd.DataFrame:
        """
        Convert a list of CommunityReport objects to a pandas DataFrame.

        Args
        ----
        reports : list[CommunityReport]
            List of CommunityReport objects.

        Returns
        -------
        pd.DataFrame: DataFrame with report data.

        Raises
        ------
        ValueError: If some reports are missing full content or full content embeddings.
        """
        report_df = pd.DataFrame([asdict(report) for report in reports])
        missing_content_error = "Some reports are missing full content."
        missing_embedding_error = (
            "Some reports are missing full content embeddings. {missing} out of {total}"
        )

        if (
            "full_content" not in report_df.columns
            or report_df["full_content"].isna().sum() > 0
        ):
            raise ValueError(missing_content_error)

        if (
            "full_content_embedding" not in report_df.columns
            or report_df["full_content_embedding"].isna().sum() > 0
        ):
            raise ValueError(
                missing_embedding_error.format(
                    missing=report_df["full_content_embedding"].isna().sum(),
                    total=len(report_df),
                )
            )
        return report_df

    @staticmethod
    def check_query_doc_encodings(query_embedding: Any, embedding: Any) -> bool:
        """
        Check if the embeddings are compatible.

        Args
        ----
        query_embedding : Any
            Embedding of the query.
        embedding : Any
            Embedding to compare against.

        Returns
        -------
        bool: True if embeddings match, otherwise False.
        """
        return (
            query_embedding is not None
            and embedding is not None
            and isinstance(query_embedding, type(embedding))
            and len(query_embedding) == len(embedding)
            and isinstance(query_embedding[0], type(embedding[0]))
        )

    def build_context(
        self, query: str, **kwargs
    ) -> tuple[pd.DataFrame, dict[str, int]]:
        """
        Build DRIFT search context.

        Args
        ----
        query : str
            Search query string.

        Returns
        -------
        pd.DataFrame: Top-k most similar documents.
        dict[str, int]: Number of LLM calls, and prompts and output tokens.

        Raises
        ------
        ValueError: If no community reports are available, or embeddings
        are incompatible.
        """
        if self.reports is None:
            missing_reports_error = (
                "No community reports available. Please provide a list of reports."
            )
            raise ValueError(missing_reports_error)

        query_processor = PrimerQueryProcessor(
            chat_llm=self.chat_llm,
            text_embedder=self.text_embedder,
            token_encoder=self.token_encoder,
            reports=self.reports,
        )

        query_embedding, token_ct = query_processor(query)

        report_df = self.convert_reports_to_df(self.reports)

        # Check compatibility between query embedding and document embeddings
        if not self.check_query_doc_encodings(
            query_embedding, report_df["full_content_embedding"].iloc[0]
        ):
            error_message = (
                "Query and document embeddings are not compatible. "
                "Please ensure that the embeddings are of the same type and length."
            )
            raise ValueError(error_message)

        # Vectorized cosine similarity computation
        query_norm = np.linalg.norm(query_embedding)
        document_norms = np.linalg.norm(
            report_df["full_content_embedding"].to_list(), axis=1
        )
        dot_products = np.dot(
            np.vstack(report_df["full_content_embedding"].to_list()), query_embedding
        )
        report_df["similarity"] = dot_products / (document_norms * query_norm)

        # Sort by similarity and select top-k
        top_k = report_df.nlargest(self.config.drift_k_followups, "similarity")

        return top_k.loc[:, ["short_id", "community_id", "full_content"]], token_ct
