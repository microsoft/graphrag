# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""LocalSearch implementation."""

import logging
import json
import time
from collections.abc import AsyncGenerator, AsyncIterator
from typing import TYPE_CHECKING, Any

from graphrag_llm.tokenizer import Tokenizer
from graphrag_llm.utils import CompletionMessagesBuilder

from graphrag.callbacks.query_callbacks import QueryCallbacks
from graphrag.index.utils.temporal_trace import ensure_trace_id, trace_event
from graphrag.prompts.query.local_search_system_prompt import (
    LOCAL_SEARCH_SYSTEM_PROMPT,
)
from graphrag.query.context_builder.builders import LocalContextBuilder
from graphrag.query.context_builder.conversation_history import (
    ConversationHistory,
)
from graphrag.query.structured_search.base import BaseSearch, SearchResult

if TYPE_CHECKING:
    from graphrag_llm.completion import LLMCompletion
    from graphrag_llm.types import LLMCompletionChunk

logger = logging.getLogger(__name__)


class LocalSearch(BaseSearch[LocalContextBuilder]):
    """Search orchestration for local search mode."""

    def __init__(
        self,
        model: "LLMCompletion",
        context_builder: LocalContextBuilder,
        tokenizer: Tokenizer | None = None,
        system_prompt: str | None = None,
        response_type: str = "multiple paragraphs",
        callbacks: list[QueryCallbacks] | None = None,
        model_params: dict[str, Any] | None = None,
        context_builder_params: dict | None = None,
    ):
        super().__init__(
            model=model,
            context_builder=context_builder,
            tokenizer=tokenizer,
            model_params=model_params,
            context_builder_params=context_builder_params or {},
        )
        self.system_prompt = system_prompt or LOCAL_SEARCH_SYSTEM_PROMPT
        self.callbacks = callbacks or []
        self.response_type = response_type

    async def search(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        **kwargs,
    ) -> SearchResult:
        """Build local search context that fits a single context window and generate answer for the user query."""
        start_time = time.time()
        ensure_trace_id()
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
        trace_event(
            logger,
            stage="query_context",
            event="context_ready_for_answer",
            context_record_keys=list(context_result.context_records.keys()),
            llm_calls=context_result.llm_calls,
            prompt_tokens=context_result.prompt_tokens,
        )

        logger.debug("GENERATE ANSWER: %s. QUERY: %s", start_time, query)
        try:
            if "drift_query" in kwargs:
                drift_query = kwargs["drift_query"]
                search_prompt = self.system_prompt.format(
                    context_data=context_result.context_chunks,
                    response_type=self.response_type,
                    global_query=drift_query,
                    followups=kwargs.get("k_followups", 0),
                )
            else:
                search_prompt = self.system_prompt.format(
                    context_data=context_result.context_chunks,
                    response_type=self.response_type,
                )
            trace_event(
                logger,
                stage="final_answer",
                event="prompt_built",
                response_type=self.response_type,
                preview_fields={"system_prompt_preview": search_prompt, "query": query},
            )
            self._log_final_prompt_payload(
                context_records=context_result.context_records,
                query=query,
                search_prompt=search_prompt,
            )

            messages_builder = (
                CompletionMessagesBuilder()
                .add_system_message(search_prompt)
                .add_user_message(query)
            )

            full_response = ""

            response: AsyncIterator[
                LLMCompletionChunk
            ] = await self.model.completion_async(
                messages=messages_builder.build(),
                stream=True,
                **self.model_params,
            )  # type: ignore

            async for chunk in response:
                response_text = chunk.choices[0].delta.content or ""
                full_response += response_text
                for callback in self.callbacks:
                    callback.on_llm_new_token(response_text)

            llm_calls["response"] = 1
            prompt_tokens["response"] = len(self.tokenizer.encode(search_prompt))
            output_tokens["response"] = len(self.tokenizer.encode(full_response))

            for callback in self.callbacks:
                callback.on_context(context_result.context_records)
            trace_event(
                logger,
                stage="final_answer",
                event="answer_generated",
                output_tokens=output_tokens["response"],
                preview_fields={"answer_preview": full_response},
            )

            return SearchResult(
                response=full_response,
                context_data=context_result.context_records,
                context_text=context_result.context_chunks,
                completion_time=time.time() - start_time,
                llm_calls=sum(llm_calls.values()),
                prompt_tokens=sum(prompt_tokens.values()),
                output_tokens=sum(output_tokens.values()),
                llm_calls_categories=llm_calls,
                prompt_tokens_categories=prompt_tokens,
                output_tokens_categories=output_tokens,
            )

        except Exception:
            logger.exception("Exception in _asearch")
            return SearchResult(
                response="",
                context_data=context_result.context_records,
                context_text=context_result.context_chunks,
                completion_time=time.time() - start_time,
                llm_calls=1,
                prompt_tokens=len(self.tokenizer.encode(search_prompt)),
                output_tokens=0,
            )

    async def stream_search(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
    ) -> AsyncGenerator:
        """Build local search context that fits a single context window and generate answer for the user query."""
        start_time = time.time()

        context_result = self.context_builder.build_context(
            query=query,
            conversation_history=conversation_history,
            **self.context_builder_params,
        )
        logger.debug("GENERATE ANSWER: %s. QUERY: %s", start_time, query)
        search_prompt = self.system_prompt.format(
            context_data=context_result.context_chunks, response_type=self.response_type
        )
        self._log_final_prompt_payload(
            context_records=context_result.context_records,
            query=query,
            search_prompt=search_prompt,
        )

        messages_builder = (
            CompletionMessagesBuilder()
            .add_system_message(search_prompt)
            .add_user_message(query)
        )

        for callback in self.callbacks:
            callback.on_context(context_result.context_records)

        response: AsyncIterator[LLMCompletionChunk] = await self.model.completion_async(
            messages=messages_builder.build(),
            stream=True,
            **self.model_params,
        )  # type: ignore

        async for chunk in response:
            response_text = chunk.choices[0].delta.content or ""
            for callback in self.callbacks:
                callback.on_llm_new_token(response_text)
            yield response_text

    def _log_final_prompt_payload(
        self,
        context_records: dict[str, Any],
        query: str,
        search_prompt: str,
    ) -> None:
        experiment_meta_df = context_records.get("experiment_meta")
        if experiment_meta_df is None or getattr(experiment_meta_df, "empty", True):
            return

        record = experiment_meta_df.iloc[0].to_dict()
        if not bool(record.get("prompt_logging_enabled", False)):
            return
        payload = {
            "experiment_condition_id": record.get("experiment_condition_id", ""),
            "selection_policy": record.get("selection_policy", ""),
            "history_on": bool(record.get("history_enabled", False)),
            "covariate_on": bool(record.get("covariate_enabled", False)),
            "query": query,
            "selected_community_ids": (
                str(record.get("selected_community_ids", "")).split(",")
                if record.get("selected_community_ids")
                else []
            ),
            "selected_community_titles": (
                str(record.get("selected_community_titles", "")).split(",")
                if record.get("selected_community_titles")
                else []
            ),
            "warning": bool(record.get("warnings")),
            "warning_messages": record.get("warnings", ""),
            "token_count_context": len(self.tokenizer.encode(str(search_prompt))),
            "final_system_prompt": search_prompt,
        }
        logger.info("local_search_prompt_payload=%s", json.dumps(payload, ensure_ascii=False))
