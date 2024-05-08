# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The GlobalSearch Implementation."""

import asyncio
import logging
import re
import time
from dataclasses import dataclass
from typing import Any

import pandas as pd
import tiktoken

from graphrag.query.context_builder.builders import GlobalContextBuilder
from graphrag.query.context_builder.conversation_history import (
    ConversationHistory,
)
from graphrag.query.llm.base import BaseLLM
from graphrag.query.llm.text_utils import num_tokens
from graphrag.query.structured_search.base import BaseSearch, SearchResult
from graphrag.query.structured_search.global_search.callbacks import (
    GlobalSearchLLMCallback,
)
from graphrag.query.structured_search.global_search.map_system_prompt import (
    MAP_SYSTEM_PROMPT,
)
from graphrag.query.structured_search.global_search.reduce_system_prompt import (
    REDUCE_SYSTEM_PROMPT,
)

DEFAULT_MAP_LLM_PARAMS = {
    "max_tokens": 500,
    "temperature": 0.0,
}

DEFAULT_REDUCE_LLM_PARAMS = {
    "max_tokens": 1500,
    "temperature": 0.0,
}
log = logging.getLogger(__name__)


@dataclass
class GlobalSearchResult(SearchResult):
    """A GlobalSearch result."""

    map_responses: list[SearchResult]
    reduce_context_data: str | list[pd.DataFrame] | dict[str, pd.DataFrame]
    reduce_context_text: str | list[str] | dict[str, str]


class GlobalSearch(BaseSearch):
    """Search orchestration for global search mode."""

    def __init__(
        self,
        llm: BaseLLM,
        context_builder: GlobalContextBuilder,
        token_encoder: tiktoken.Encoding | None = None,  # type: ignore
        map_system_prompt: str = MAP_SYSTEM_PROMPT,
        reduce_system_prompt: str = REDUCE_SYSTEM_PROMPT,
        response_type: str = "multiple paragraphs",
        callbacks: list[GlobalSearchLLMCallback] | None = None,
        max_data_tokens: int = 8000,
        map_llm_params: dict[str, Any] = DEFAULT_MAP_LLM_PARAMS,
        reduce_llm_params: dict[str, Any] = DEFAULT_REDUCE_LLM_PARAMS,
        context_builder_params: dict[str, Any] | None = None,
        concurrent_coroutines: int = 32,
    ):
        super().__init__(
            llm=llm,
            context_builder=context_builder,
            token_encoder=token_encoder,
            context_builder_params=context_builder_params,
        )
        self.map_system_prompt = map_system_prompt
        self.reduce_system_prompt = reduce_system_prompt
        self.response_type = response_type
        self.callbacks = callbacks
        self.max_data_tokens = max_data_tokens
        self.map_llm_params = map_llm_params
        self.reduce_llm_params = reduce_llm_params
        self.semaphore = asyncio.Semaphore(concurrent_coroutines)

    async def asearch(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        **kwargs: Any,
    ) -> GlobalSearchResult:
        """
        Perform a global search.

        Global search mode includes two steps:

        - Step 1: Run parallel LLM calls on communities' short summaries to generate answer for each batch
        - Step 2: Combine the answers from step 2 to generate the final answer
        """
        # Step 1: Generate answers for each batch of community short summaries
        start_time = time.time()
        context_chunks, context_records = self.context_builder.build_context(
            conversation_history=conversation_history, **self.context_builder_params
        )

        if self.callbacks:
            for callback in self.callbacks:
                callback.on_map_response_start(context_chunks)  # type: ignore
        map_responses = await asyncio.gather(*[
            self._map_response_single_batch(
                context_data=data, query=query, **self.map_llm_params
            )
            for data in context_chunks
        ])
        if self.callbacks:
            for callback in self.callbacks:
                callback.on_map_response_end(map_responses)
        map_llm_calls = sum(response.llm_calls for response in map_responses)
        map_prompt_tokens = sum(response.prompt_tokens for response in map_responses)

        # Step 2: Combine the intermediate answers from step 2 to generate the final answer
        reduce_response = await self._reduce_response(
            map_responses=map_responses,
            query=query,
            **self.reduce_llm_params,
        )

        return GlobalSearchResult(
            response=reduce_response.response,
            context_data=context_records,
            context_text=context_chunks,
            map_responses=map_responses,
            reduce_context_data=reduce_response.context_data,
            reduce_context_text=reduce_response.context_text,
            completion_time=time.time() - start_time,
            llm_calls=map_llm_calls + reduce_response.llm_calls,
            prompt_tokens=map_prompt_tokens + reduce_response.prompt_tokens,
        )

    def search(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        **kwargs: Any,
    ) -> GlobalSearchResult:
        """Perform a global search synchronously."""
        return asyncio.run(self.asearch(query, conversation_history))

    async def _map_response_single_batch(
        self,
        context_data: str,
        query: str,
        ranking_delimiter: str = "</ANSWER_HELPFULNESS>",
        **llm_kwargs,
    ) -> SearchResult:
        """Generate answer for a single chunk of community reports."""
        start_time = time.time()
        search_prompt = ""
        try:
            search_prompt = self.map_system_prompt.format(
                context_data=context_data, response_type=self.response_type
            )
            search_messages = [
                {"role": "system", "content": search_prompt},
                {"role": "user", "content": query},
            ]
            async with self.semaphore:
                search_response = await self.llm.agenerate(
                    messages=search_messages, streaming=False, **llm_kwargs
                )
                parsed_response = search_response.split(ranking_delimiter)
            try:
                if len(parsed_response) > 1:
                    processed_response = {
                        "answer": parsed_response[1].strip(),
                        "score": int(re.findall("\\d+", parsed_response[0])[0]),
                    }
                else:
                    processed_response = {
                        "answer": search_response,
                        "score": 50,  # default to mean score
                    }
            except Exception:  # noqa BLE001
                processed_response = {"answer": search_response, "score": 50}

            return SearchResult(
                response=processed_response,
                context_data=context_data,
                context_text=context_data,
                completion_time=time.time() - start_time,
                llm_calls=1,
                prompt_tokens=num_tokens(search_prompt, self.token_encoder),
            )

        except Exception:
            log.exception("Exception in _map_response_single_batch")
            return SearchResult(
                response={"answer": "", "score": 0},
                context_data=context_data,
                context_text=context_data,
                completion_time=time.time() - start_time,
                llm_calls=1,
                prompt_tokens=num_tokens(search_prompt, self.token_encoder),
            )

    async def _reduce_response(
        self,
        map_responses: list[SearchResult],
        query: str,
        **llm_kwargs,
    ) -> SearchResult:
        """Combine all intermediate responses from single batches into a final answer to the user query."""
        text_data = ""
        search_prompt = ""
        start_time = time.time()
        try:
            # filter response with score = 0 and rank responses by descending order of score
            filtered_map_responses = [
                response
                for response in map_responses
                if response.response["score"] > 0  # type: ignore
            ]
            filtered_map_responses = sorted(
                filtered_map_responses,
                key=lambda x: x.response["score"],  # type: ignore
                reverse=True,  # type: ignore
            )

            data = []
            total_tokens = 0
            for index, response in enumerate(filtered_map_responses):
                formatted_response_data = []
                formatted_response_data.append(f"-----Analyst {index + 1}-----")
                formatted_response_data.append(
                    f'Helpfulness Score: {response.response["score"]}'  # type: ignore
                )
                formatted_response_data.append(response.response["answer"])  # type: ignore
                formatted_response_text = "\n".join(formatted_response_data)
                if (
                    total_tokens
                    + num_tokens(formatted_response_text, self.token_encoder)
                    > self.max_data_tokens
                ):
                    break
                data.append(formatted_response_text)
                total_tokens += num_tokens(formatted_response_text, self.token_encoder)
            text_data = "\n\n".join(data)
            search_prompt = self.reduce_system_prompt.format(
                report_data=text_data, response_type=self.response_type
            )
            search_messages = [
                {"role": "system", "content": search_prompt},
                {"role": "user", "content": query},
            ]

            search_response = await self.llm.agenerate(
                search_messages,
                streaming=True,
                callbacks=self.callbacks,  # type: ignore
                **llm_kwargs,  # type: ignore
            )
            return SearchResult(
                response=search_response,
                context_data=text_data,
                context_text=text_data,
                completion_time=time.time() - start_time,
                llm_calls=1,
                prompt_tokens=num_tokens(search_prompt, self.token_encoder),
            )
        except Exception:
            log.exception("Exception in reduce_response")
            return SearchResult(
                response="",
                context_data=text_data,
                context_text=text_data,
                completion_time=time.time() - start_time,
                llm_calls=1,
                prompt_tokens=num_tokens(search_prompt, self.token_encoder),
            )
