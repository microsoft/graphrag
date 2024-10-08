import logging
from typing import Any, List

import numpy as np
import pandas as pd
import tiktoken

from graphrag.config.models.drift_config import DRIFTSearchConfig
from graphrag.model import (
    CommunityReport,
    Covariate,
    Entity,
    Relationship,
    TextUnit,
)
from graphrag.query.context_builder.entity_extraction import EntityVectorStoreKey
from graphrag.query.llm.base import BaseTextEmbedding
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
from graphrag.query.structured_search.base import DRIFTContextBuilder
from graphrag.query.structured_search.drift_search.primer import (
    PrimerQueryProcessor,
)
from graphrag.query.structured_search.drift_search.system_prompt import (
    DRIFT_LOCAL_SYSTEM_PROMPT,
)
from graphrag.query.structured_search.local_search.mixed_context import (
    LocalSearchMixedContext,
)
from graphrag.vector_stores import BaseVectorStore

log = logging.getLogger(__name__)


class DRIFTSearchContextBuilder(DRIFTContextBuilder):
    def __init__(
        self,
        chat_llm: ChatOpenAI,
        text_embedder: BaseTextEmbedding,
        entities: List[Entity],
        entity_text_embeddings: BaseVectorStore,
        text_units: List[TextUnit] | None = None,
        reports: List[CommunityReport] | None = None,
        relationships: List[Relationship] | None = None,
        covariates: dict[str, List[Covariate]] | None = None,
        token_encoder: tiktoken.Encoding | None = None,
        embedding_vectorstore_key: str = EntityVectorStoreKey.ID,
        config: DRIFTSearchConfig | None = None,
        local_system_prompt: str = DRIFT_LOCAL_SYSTEM_PROMPT,
        local_mixed_context: LocalSearchMixedContext | None = None,
    ):
        self.config = config or DRIFTSearchConfig()
        self.chat_llm = chat_llm
        self.text_embedder = text_embedder
        self.token_encoder = token_encoder
        self.local_system_prompt = local_system_prompt

        self.drift_primer_context = None

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
    def convert_reports_to_df(
        reports: List[CommunityReport],
    ) -> pd.DataFrame:
        """
        Converts a list of CommunityReport objects to a DataFrame.
        """
        df = pd.DataFrame([report.__dict__ for report in reports])
        if df["full_content"].isnull().any():
            raise ValueError("Some reports are missing full content.")

        if (
            "full_content_embedding" not in df.columns
            or df["full_content_embedding"].isnull().any()
        ):
            raise ValueError("Some reports are missing full content embeddings.")

        return df

    @staticmethod
    def check_query_doc_encodings(
        query_embedding: Any, embedding: Any
    ) -> bool:
        """
        Checks if the embeddings have the same type, length, are not empty,
        and have matching element types.
        """
        if not (
            isinstance(query_embedding, type(embedding))
            and len(query_embedding) == len(embedding)
            and isinstance(query_embedding[0], type(embedding[0]))
        ):
            return False
        return True

    def build_primer_context(self, query: str, **kwargs) -> pd.DataFrame:
        if not self.reports:
            raise ValueError(
                "No community reports available... Please provide a list of reports."
            )

        query_processor = PrimerQueryProcessor(
            chat_llm=self.chat_llm,
            text_embedder=self.text_embedder,
            token_encoder=self.token_encoder,
            reports=self.reports,
        )

        query_embedding = query_processor(query)

        report_df = self.convert_reports_to_df(self.reports)

        if self.check_query_doc_encodings(
            query_embedding, report_df["full_content_embedding"].iloc[0]
        ):
            report_df["similarity"] = report_df[
                "full_content_embedding"
            ].apply(
                lambda x: np.dot(x, query_embedding)
                / (np.linalg.norm(x) * np.linalg.norm(query_embedding))
            )
            top_k = (
                report_df.sort_values("similarity", ascending=False)
                .head(self.config.search_primer_k)
            )
        else:
            raise ValueError(
                "Query and document embeddings are not compatible. "
                "Please ensure that the embeddings are of the same type and length."
                f"  Query: {query_embedding}, Document: {report_df['full_content_embedding'].iloc[0]}"
            )

        return top_k[['short_id', 'community_id', 'full_content']]

