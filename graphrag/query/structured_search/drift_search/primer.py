# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Primer for DRIFT search."""

import json
import logging
import secrets
import time

import numpy as np
import pandas as pd
import tiktoken
from tqdm.asyncio import tqdm_asyncio

from graphrag.config.models.drift_search_config import DRIFTSearchConfig
from graphrag.data_model.community_report import CommunityReport
from graphrag.language_model.protocol.base import ChatModel, EmbeddingModel
from graphrag.prompts.query.drift_search_system_prompt import (
    DRIFT_PRIMER_PROMPT,
)
from graphrag.query.llm.text_utils import num_tokens
from graphrag.query.structured_search.base import SearchResult

log = logging.getLogger(__name__)


class PrimerQueryProcessor:
    """Process the query by expanding it using community reports and generate follow-up actions."""

    def __init__(
        self,
        chat_model: ChatModel,
        text_embedder: EmbeddingModel,
        reports: list[CommunityReport],
        token_encoder: tiktoken.Encoding | None = None,
    ):
        """
        Initialize the PrimerQueryProcessor.

        Args:
            chat_llm (ChatOpenAI): The language model used to process the query.
            text_embedder (BaseTextEmbedding): The text embedding model.
            reports (list[CommunityReport]): List of community reports.
            token_encoder (tiktoken.Encoding, optional): Token encoder for token counting.
        """
        self.chat_model = chat_model
        self.text_embedder = text_embedder
        self.token_encoder = token_encoder
        self.reports = reports

    async def expand_query(self, query: str) -> tuple[str, dict[str, int]]:
        """
        Expand the query using a random community report template.

        Args:
            query (str): The original search query.

        Returns
        -------
        tuple[str, dict[str, int]]: Expanded query text and the number of tokens used.
        """
        template = secrets.choice(self.reports).full_content  # nosec S311

        prompt = f"""Create a hypothetical answer to the following query: {query}\n\n
                  Format it to follow the structure of the template below:\n\n
                  {template}\n"
                  Ensure that the hypothetical answer does not reference new named entities that are not present in the original query."""

        model_response = await self.chat_model.achat(prompt)
        text = model_response.output.content

        prompt_tokens = num_tokens(prompt, self.token_encoder)
        output_tokens = num_tokens(text, self.token_encoder)
        token_ct = {
            "llm_calls": 1,
            "prompt_tokens": prompt_tokens,
            "output_tokens": output_tokens,
        }
        if text == "":
            log.warning("Failed to generate expansion for query: %s", query)
            return query, token_ct
        return text, token_ct

    async def __call__(self, query: str) -> tuple[list[float], dict[str, int]]:
        """
        Call method to process the query, expand it, and embed the result.

        Args:
            query (str): The search query.

        Returns
        -------
        tuple[list[float], int]: List of embeddings for the expanded query and the token count.
        """
        hyde_query, token_ct = await self.expand_query(query)
        log.info("Expanded query: %s", hyde_query)
        return self.text_embedder.embed(hyde_query), token_ct


class DRIFTPrimer:
    """Perform initial query decomposition using global guidance from information in community reports."""

    def __init__(
        self,
        config: DRIFTSearchConfig,
        chat_model: ChatModel,
        token_encoder: tiktoken.Encoding | None = None,
    ):
        """
        Initialize the DRIFTPrimer.

        Args:
            config (DRIFTSearchConfig): Configuration settings for DRIFT search.
            chat_llm (ChatOpenAI): The language model used for searching.
            token_encoder (tiktoken.Encoding, optional): Token encoder for managing tokens.
        """
        self.chat_model = chat_model
        self.config = config
        self.token_encoder = token_encoder

    async def decompose_query(
        self, query: str, reports: pd.DataFrame
    ) -> tuple[dict, dict[str, int]]:
        """
        Decompose the query into subqueries based on the fetched global structures.

        Args:
            query (str): The original search query.
            reports (pd.DataFrame): DataFrame containing community reports.

        Returns
        -------
        tuple[dict, int, int]: Parsed response and the number of prompt and output tokens used.
        """
        community_reports = "\n\n".join(reports["full_content"].tolist())
        prompt = DRIFT_PRIMER_PROMPT.format(
            query=query, community_reports=community_reports
        )
        model_response = await self.chat_model.achat(prompt, json=True)
        response = model_response.output.content

        parsed_response = json.loads(response)

        token_ct = {
            "llm_calls": 1,
            "prompt_tokens": num_tokens(prompt, self.token_encoder),
            "output_tokens": num_tokens(response, self.token_encoder),
        }

        return parsed_response, token_ct

    async def search(
        self,
        query: str,
        top_k_reports: pd.DataFrame,
    ) -> SearchResult:
        """
        Asynchronous search method that processes the query and returns a SearchResult.

        Args:
            query (str): The search query.
            top_k_reports (pd.DataFrame): DataFrame containing the top-k reports.

        Returns
        -------
        SearchResult: The search result containing the response and context data.
        """
        start_time = time.perf_counter()
        report_folds = self.split_reports(top_k_reports)
        tasks = [self.decompose_query(query, fold) for fold in report_folds]

        results_with_tokens = await tqdm_asyncio.gather(*tasks, leave=False)

        completion_time = time.perf_counter() - start_time

        return SearchResult(
            response=[response for response, _ in results_with_tokens],
            context_data={"top_k_reports": top_k_reports},
            context_text=top_k_reports.to_json() or "",
            completion_time=completion_time,
            llm_calls=len(results_with_tokens),
            prompt_tokens=sum(ct["prompt_tokens"] for _, ct in results_with_tokens),
            output_tokens=sum(ct["output_tokens"] for _, ct in results_with_tokens),
        )

    def split_reports(self, reports: pd.DataFrame) -> list[pd.DataFrame]:
        """
        Split the reports into folds, allowing for parallel processing.

        Args:
            reports (pd.DataFrame): DataFrame of community reports.

        Returns
        -------
        list[pd.DataFrame]: List of report folds.
        """
        primer_folds = self.config.primer_folds or 1  # Ensure at least one fold
        if primer_folds == 1:
            return [reports]
        return [pd.DataFrame(fold) for fold in np.array_split(reports, primer_folds)]
