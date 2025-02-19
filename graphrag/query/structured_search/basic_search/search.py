# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""BasicSearch implementation."""

import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

import tiktoken

from graphrag.callbacks.query_callbacks import QueryCallbacks
from graphrag.prompts.query.basic_search_system_prompt import (
    BASIC_SEARCH_SYSTEM_PROMPT,
)
from graphrag.query.context_builder.builders import BasicContextBuilder
from graphrag.query.context_builder.conversation_history import ConversationHistory
from graphrag.query.llm.base import BaseLLM
from graphrag.query.llm.text_utils import num_tokens
from graphrag.query.structured_search.base import BaseSearch, SearchResult

DEFAULT_LLM_PARAMS = {
    "max_tokens": 1500,
    "temperature": 0.0,
}

log = logging.getLogger(__name__)
"""
Implementation of a generic RAG algorithm (vector search on raw text chunks)
"""


class BasicSearch(BaseSearch[BasicContextBuilder]):
    """Search orchestration for basic search mode."""

    def __init__(
        self,
        llm: BaseLLM,
        context_builder: BasicContextBuilder,
        token_encoder: tiktoken.Encoding | None = None,
        system_prompt: str | None = None,
        response_type: str = "multiple paragraphs",
        callbacks: list[QueryCallbacks] | None = None,
        llm_params: dict[str, Any] = DEFAULT_LLM_PARAMS,
        context_builder_params: dict | None = None,
    ):
        super().__init__(
            llm=llm,
            context_builder=context_builder,
            token_encoder=token_encoder,
            llm_params=llm_params,
            context_builder_params=context_builder_params or {},
        )
        self.system_prompt = system_prompt or BASIC_SEARCH_SYSTEM_PROMPT
        self.callbacks = callbacks or []
        self.response_type = response_type

    async def search(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        **kwargs,
    ) -> SearchResult:
        """Build rag search context that fits a single context window and generate answer for the user query."""
        start_time = time.time()
        search_prompt = ""
        llm_calls, prompt_tokens, output_tokens = {}, {}, {}

        context_result = self.context_builder.build_context(
            query=query,
            conversation_history=conversation_history,
            **kwargs,
            **self.context_builder_params,
        )

        llm_calls["build_context"] = context_result.llm_calls
        prompt_tokens["build_context"] = context_result.prompt_tokens
        output_tokens["build_context"] = context_result.output_tokens

        log.info("GENERATE ANSWER: %s. QUERY: %s", start_time, query)
        try:
            search_prompt = self.system_prompt.format(
                context_data=context_result.context_chunks,
                response_type=self.response_type,
            )
            search_messages = [
                {"role": "system", "content": search_prompt},
                {"role": "user", "content": query},
            ]

            response = await self.llm.agenerate(
                messages=search_messages,
                streaming=True,
                callbacks=self.callbacks,  # type: ignore
                **self.llm_params,
            )

            llm_calls["response"] = 1
            prompt_tokens["response"] = num_tokens(search_prompt, self.token_encoder)
            output_tokens["response"] = num_tokens(response, self.token_encoder)

            for callback in self.callbacks:
                callback.on_context(context_result.context_records)

            return SearchResult(
                response=response,
                context_data=context_result.context_records,
                context_text=context_result.context_chunks,
                completion_time=time.time() - start_time,
                llm_calls=1,
                prompt_tokens=num_tokens(search_prompt, self.token_encoder),
                output_tokens=sum(output_tokens.values()),
            )

        except Exception:
            log.exception("Exception in _asearch")
            return SearchResult(
                response="",
                context_data=context_result.context_records,
                context_text=context_result.context_chunks,
                completion_time=time.time() - start_time,
                llm_calls=1,
                prompt_tokens=num_tokens(search_prompt, self.token_encoder),
                output_tokens=0,
            )

    def stream_search(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
    ) -> AsyncGenerator[Any, None]:
        """Build basic search context that fits a single context window and generate answer for the user query."""
        start_time = time.time()

        context_result = self.context_builder.build_context(
            query=query,
            conversation_history=conversation_history,
            **self.context_builder_params,
        )
        log.info("GENERATE ANSWER: %s. QUERY: %s", start_time, query)
        search_prompt = self.system_prompt.format(
            context_data=context_result.context_chunks, response_type=self.response_type
        )
        search_messages = [
            {"role": "system", "content": search_prompt},
            {"role": "user", "content": query},
        ]

        for callback in self.callbacks:
            callback.on_context(context_result.context_records)

        return self.llm.astream_generate(  # type: ignore
            messages=search_messages,
            callbacks=self.callbacks,  # type: ignore
            **self.llm_params,
        )
