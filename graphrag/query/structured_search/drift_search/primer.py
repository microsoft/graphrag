import logging
import json
import pandas as pd
import random
import time
from typing import Any, List, Dict, Tuple

import tiktoken
from tqdm.asyncio import tqdm_asyncio

from graphrag.config.models.drift_config import DRIFTSearchConfig
from graphrag.model import CommunityReport
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
from graphrag.query.llm.base import BaseTextEmbedding
from graphrag.query.structured_search.base import SearchResult
from graphrag.query.structured_search.drift_search.system_prompt import DRIFT_PRIMER_PROMPT

log = logging.getLogger(__name__)


class PrimerQueryProcessor:

    def __init__(self, chat_llm: ChatOpenAI, text_embedder: BaseTextEmbedding, reports: List[CommunityReport], token_encoder: tiktoken.Encoding | None = None,):
        self.chat_llm = chat_llm
        self.text_embedder = text_embedder
        self.token_encoder = token_encoder
        self.reports = reports

    def expand_query(self, query: str) -> Tuple[str, int]:
        token_ct = 0

        template = random.choice(self.reports).full_content

        prompt = (
            f"Create a hypothetical answer to the following query: {query}\n\n"
            "Format it to follow the structure of the template below:\n\n"
            f"{template}\n"
            "Ensure that the hypothetical answer does not reference new named entities that are not present in the original query."
        )
        messages = [
            {"role": "user", "content": prompt}
        ]

        text = self.chat_llm.generate(messages)
        if self.token_encoder:
            token_ct = len(self.token_encoder.encode(text)) + len(self.token_encoder.encode(query))
        if text == "":
            log.warning("Failed to generate expansion for query: %s", query)
            return query, token_ct
        return text, token_ct

    def __call__(self, query: str) -> List[float]:
        hyde_query, token_ct = self.expand_query(query) # TODO: implement token counting
        log.info("Expanded query: %s", hyde_query)
        return self.text_embedder.embed(hyde_query)


class DRIFTPrimer:
    """
    Performs initial query decomposition using global guidance from information in community reports.
    """

    def __init__(
        self,
        config: DRIFTSearchConfig,
        chat_llm: ChatOpenAI,
        token_encoder: tiktoken.Encoding | None = None, # TODO: implement token counting
    ):
        self.llm = chat_llm
        self.config = config
        self.token_encoder = token_encoder


    async def decompose_query(self, query: str, reports: pd.DataFrame) -> Tuple[Dict, int]:
        """
        Decomposes the query into subqueries based on the fetched global structures.
        Returns a tuple of the parsed response and the number of tokens used.
        """
        community_reports = "\n\n".join(reports['full_content'].tolist())
        prompt = DRIFT_PRIMER_PROMPT.format(query=query, community_reports=community_reports)
        messages = [{"role": "user", "content": prompt}]

        prompt_tokens = self._count_message_tokens(messages)

        response = await self.llm.agenerate(messages, response_format={"type": "json_object"})

        parsed_response = json.loads(response)

        return parsed_response, prompt_tokens


    async def asearch(
        self,
        query: str,
        top_k_reports: pd.DataFrame,
    ) -> SearchResult:
        """
        Asynchronous search method that processes the query and returns a SearchResult.
        """
        start_time = time.time()

        report_folds = self.split_reports(top_k_reports)

        tasks = []
        prompt_tokens = 0
        llm_calls = len(report_folds)

        for fold in report_folds:
            task = self.decompose_query(query, fold)
            tasks.append(task)

        results_with_tokens = await tqdm_asyncio.gather(*tasks)

        for result in results_with_tokens:
            # result is a tuple: (parsed_response, tokens_used)
            _, tokens_used = result
            prompt_tokens += tokens_used       
        completion_time = time.time() - start_time

        search_result = SearchResult(
            response=[response for response, _ in results_with_tokens],
            context_data={'top_k_reports': top_k_reports},
            context_text=str(top_k_reports),
            completion_time=completion_time,
            llm_calls=llm_calls,
            prompt_tokens=prompt_tokens,
        )
        return search_result


    def split_reports(self, reports: pd.DataFrame) -> List[pd.DataFrame]:
        """
        Splits the reports into folds, allows for parallel processing.
        """
        folds = []
        num_reports = len(reports)
        primer_folds = self.config.primer_folds or 1  # Ensure at least one fold
        for i in range(primer_folds):
            start_idx = i * num_reports // primer_folds
            if i == primer_folds - 1:
                end_idx = num_reports
            else:
                end_idx = (i + 1) * num_reports // primer_folds
            fold = reports.iloc[start_idx:end_idx]
            folds.append(fold)
        return folds


    def _count_text_tokens(self, text: str) -> int:
        """
        Counts the number of tokens in a given text using the token encoder.
        """
        if self.token_encoder is None:
            raise ValueError("Token encoder is not initialized.")
        return len(self.token_encoder.encode(text))

    def _count_message_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        Counts the number of tokens in a list of messages.
        """
        total_tokens = 0
        for message in messages:
            for _, value in message.items():
                total_tokens += self._count_text_tokens(value)
        return total_tokens
