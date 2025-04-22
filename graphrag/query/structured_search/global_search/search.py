# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""The GlobalSearch Implementation."""

import asyncio
import json
import logging
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any

import pandas as pd
import tiktoken

from graphrag.callbacks.query_callbacks import QueryCallbacks
from graphrag.language_model.protocol.base import ChatModel
from graphrag.prompts.query.global_search_knowledge_system_prompt import (
    GENERAL_KNOWLEDGE_INSTRUCTION,
)
from graphrag.prompts.query.global_search_map_system_prompt import (
    MAP_SYSTEM_PROMPT,
)
from graphrag.prompts.query.global_search_reduce_system_prompt import (
    NO_DATA_ANSWER,
    REDUCE_SYSTEM_PROMPT,
)
from graphrag.query.context_builder.builders import GlobalContextBuilder
from graphrag.query.context_builder.conversation_history import (
    ConversationHistory,
)
from graphrag.query.llm.text_utils import num_tokens, try_parse_json_object
from graphrag.query.structured_search.base import BaseSearch, SearchResult

log = logging.getLogger(__name__)


@dataclass(kw_only=True)
class GlobalSearchResult(SearchResult):
    """A GlobalSearch result."""

    map_responses: list[SearchResult]
    reduce_context_data: str | list[pd.DataFrame] | dict[str, pd.DataFrame]
    reduce_context_text: str | list[str] | dict[str, str]


class GlobalSearch(BaseSearch[GlobalContextBuilder]):
    """Search orchestration for global search mode."""

    def __init__(
        self,
        model: ChatModel,
        context_builder: GlobalContextBuilder,
        token_encoder: tiktoken.Encoding | None = None,
        map_system_prompt: str | None = None,
        reduce_system_prompt: str | None = None,
        response_type: str = "multiple paragraphs",
        allow_general_knowledge: bool = False,
        general_knowledge_inclusion_prompt: str | None = None,
        json_mode: bool = True,
        callbacks: list[QueryCallbacks] | None = None,
        max_data_tokens: int = 8000,
        map_llm_params: dict[str, Any] | None = None,
        reduce_llm_params: dict[str, Any] | None = None,
        map_max_length: int = 1000,
        reduce_max_length: int = 2000,
        context_builder_params: dict[str, Any] | None = None,
        concurrent_coroutines: int = 32,
    ):
        super().__init__(
            model=model,
            context_builder=context_builder,
            token_encoder=token_encoder,
            context_builder_params=context_builder_params,
        )
        self.map_system_prompt = map_system_prompt or MAP_SYSTEM_PROMPT
        self.reduce_system_prompt = reduce_system_prompt or REDUCE_SYSTEM_PROMPT
        self.response_type = response_type
        self.allow_general_knowledge = allow_general_knowledge
        self.general_knowledge_inclusion_prompt = (
            general_knowledge_inclusion_prompt or GENERAL_KNOWLEDGE_INSTRUCTION
        )
        self.callbacks = callbacks or []
        self.max_data_tokens = max_data_tokens

        self.map_llm_params = map_llm_params if map_llm_params else {}
        self.reduce_llm_params = reduce_llm_params if reduce_llm_params else {}
        if json_mode:
            self.map_llm_params["response_format"] = {"type": "json_object"}
        else:
            # remove response_format key if json_mode is False
            self.map_llm_params.pop("response_format", None)
        self.map_max_length = map_max_length
        self.reduce_max_length = reduce_max_length

        self.semaphore = asyncio.Semaphore(concurrent_coroutines)

    async def stream_search(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream the global search response."""
        context_result = await self.context_builder.build_context(
            query=query,
            conversation_history=conversation_history,
            **self.context_builder_params,
        )
        for callback in self.callbacks:
            callback.on_map_response_start(context_result.context_chunks)  # type: ignore

        map_responses = await asyncio.gather(*[
            self._map_response_single_batch(
                context_data=data,
                query=query,
                max_length=self.map_max_length,
                **self.map_llm_params,
            )
            for data in context_result.context_chunks
        ])

        for callback in self.callbacks:
            callback.on_map_response_end(map_responses)  # type: ignore
            callback.on_context(context_result.context_records)

        async for response in self._stream_reduce_response(
            map_responses=map_responses,  # type: ignore
            query=query,
            max_length=self.reduce_max_length,
            model_parameters=self.reduce_llm_params,
        ):
            yield response

    async def search(
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
        llm_calls, prompt_tokens, output_tokens = {}, {}, {}

        start_time = time.time()
        context_result = await self.context_builder.build_context(
            query=query,
            conversation_history=conversation_history,
            **self.context_builder_params,
        )
        llm_calls["build_context"] = context_result.llm_calls
        prompt_tokens["build_context"] = context_result.prompt_tokens
        output_tokens["build_context"] = context_result.output_tokens

        for callback in self.callbacks:
            callback.on_map_response_start(context_result.context_chunks)  # type: ignore

        map_responses = await asyncio.gather(*[
            self._map_response_single_batch(
                context_data=data,
                query=query,
                max_length=self.map_max_length,
                **self.map_llm_params,
            )
            for data in context_result.context_chunks
        ])

        for callback in self.callbacks:
            callback.on_map_response_end(map_responses)
            callback.on_context(context_result.context_records)

        llm_calls["map"] = sum(response.llm_calls for response in map_responses)
        prompt_tokens["map"] = sum(response.prompt_tokens for response in map_responses)
        output_tokens["map"] = sum(response.output_tokens for response in map_responses)

        # Step 2: Combine the intermediate answers from step 2 to generate the final answer
        reduce_response = await self._reduce_response(
            map_responses=map_responses,
            query=query,
            **self.reduce_llm_params,
        )
        llm_calls["reduce"] = reduce_response.llm_calls
        prompt_tokens["reduce"] = reduce_response.prompt_tokens
        output_tokens["reduce"] = reduce_response.output_tokens

        return GlobalSearchResult(
            response=reduce_response.response,
            context_data=context_result.context_records,
            context_text=context_result.context_chunks,
            map_responses=map_responses,
            reduce_context_data=reduce_response.context_data,
            reduce_context_text=reduce_response.context_text,
            completion_time=time.time() - start_time,
            llm_calls=sum(llm_calls.values()),
            prompt_tokens=sum(prompt_tokens.values()),
            output_tokens=sum(output_tokens.values()),
            llm_calls_categories=llm_calls,
            prompt_tokens_categories=prompt_tokens,
            output_tokens_categories=output_tokens,
        )

    async def _map_response_single_batch(
        self,
        context_data: str,
        query: str,
        max_length: int,
        **llm_kwargs,
    ) -> SearchResult:
        """Generate answer for a single chunk of community reports."""
        start_time = time.time()
        search_prompt = ""
        try:
            search_prompt = self.map_system_prompt.format(
                context_data=context_data, max_length=max_length
            )
            search_messages = [
                {"role": "system", "content": search_prompt},
            ]
            async with self.semaphore:
                model_response = await self.model.achat(
                    prompt=query,
                    history=search_messages,
                    model_parameters=llm_kwargs,
                    json=True,
                )
                search_response = model_response.output.content
                log.info("Map response: %s", search_response)
            try:
                # parse search response json
                processed_response = self._parse_search_response(search_response)
            except ValueError:
                log.warning(
                    "Warning: Error parsing search response json - skipping this batch"
                )
                processed_response = []

            return SearchResult(
                response=processed_response,
                context_data=context_data,
                context_text=context_data,
                completion_time=time.time() - start_time,
                llm_calls=1,
                prompt_tokens=num_tokens(search_prompt, self.token_encoder),
                output_tokens=num_tokens(search_response, self.token_encoder),
            )

        except Exception:
            log.exception("Exception in _map_response_single_batch")
            return SearchResult(
                response=[{"answer": "", "score": 0}],
                context_data=context_data,
                context_text=context_data,
                completion_time=time.time() - start_time,
                llm_calls=1,
                prompt_tokens=num_tokens(search_prompt, self.token_encoder),
                output_tokens=0,
            )

    def _parse_search_response(self, search_response: str) -> list[dict[str, Any]]:
        """Parse the search response json and return a list of key points.

        Parameters
        ----------
        search_response: str
            The search response json string

        Returns
        -------
        list[dict[str, Any]]
            A list of key points, each key point is a dictionary with "answer" and "score" keys
        """
        search_response, j = try_parse_json_object(search_response)
        if j == {}:
            return [{"answer": "", "score": 0}]

        parsed_elements = json.loads(search_response).get("points")
        if not parsed_elements or not isinstance(parsed_elements, list):
            return [{"answer": "", "score": 0}]

        return [
            {
                "answer": element["description"],
                "score": int(element["score"]),
            }
            for element in parsed_elements
            if "description" in element and "score" in element
        ]

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
            # collect all key points into a single list to prepare for sorting
            key_points = []
            for index, response in enumerate(map_responses):
                if not isinstance(response.response, list):
                    continue
                for element in response.response:
                    if not isinstance(element, dict):
                        continue
                    if "answer" not in element or "score" not in element:
                        continue
                    key_points.append({
                        "analyst": index,
                        "answer": element["answer"],
                        "score": element["score"],
                    })

            # filter response with score = 0 and rank responses by descending order of score
            filtered_key_points = [
                point
                for point in key_points
                if point["score"] > 0  # type: ignore
            ]

            if len(filtered_key_points) == 0 and not self.allow_general_knowledge:
                # return no data answer if no key points are found
                log.warning(
                    "Warning: All map responses have score 0 (i.e., no relevant information found from the dataset), returning a canned 'I do not know' answer. You can try enabling `allow_general_knowledge` to encourage the LLM to incorporate relevant general knowledge, at the risk of increasing hallucinations."
                )
                return SearchResult(
                    response=NO_DATA_ANSWER,
                    context_data="",
                    context_text="",
                    completion_time=time.time() - start_time,
                    llm_calls=0,
                    prompt_tokens=0,
                    output_tokens=0,
                )

            filtered_key_points = sorted(
                filtered_key_points,
                key=lambda x: x["score"],  # type: ignore
                reverse=True,  # type: ignore
            )

            data = []
            total_tokens = 0
            for point in filtered_key_points:
                formatted_response_data = []
                formatted_response_data.append(
                    f"----Analyst {point['analyst'] + 1}----"
                )
                formatted_response_data.append(
                    f"Importance Score: {point['score']}"  # type: ignore
                )
                formatted_response_data.append(point["answer"])  # type: ignore
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
            if self.allow_general_knowledge:
                search_prompt += "\n" + self.general_knowledge_inclusion_prompt
            search_messages = [
                {"role": "system", "content": search_prompt},
                {"role": "user", "content": query},
            ]

            search_response = ""
            async for chunk_response in self.model.achat_stream(
                prompt=query,
                history=search_messages,
                model_parameters=llm_kwargs,
            ):
                search_response += chunk_response
                for callback in self.callbacks:
                    callback.on_llm_new_token(chunk_response)

            return SearchResult(
                response=search_response,
                context_data=text_data,
                context_text=text_data,
                completion_time=time.time() - start_time,
                llm_calls=1,
                prompt_tokens=num_tokens(search_prompt, self.token_encoder),
                output_tokens=num_tokens(search_response, self.token_encoder),
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
                output_tokens=0,
            )

    async def _stream_reduce_response(
        self,
        map_responses: list[SearchResult],
        query: str,
        max_length: int,
        **llm_kwargs,
    ) -> AsyncGenerator[str, None]:
        # collect all key points into a single list to prepare for sorting
        key_points = []
        for index, response in enumerate(map_responses):
            if not isinstance(response.response, list):
                continue
            for element in response.response:
                if not isinstance(element, dict):
                    continue
                if "answer" not in element or "score" not in element:
                    continue
                key_points.append({
                    "analyst": index,
                    "answer": element["answer"],
                    "score": element["score"],
                })

        # filter response with score = 0 and rank responses by descending order of score
        filtered_key_points = [
            point
            for point in key_points
            if point["score"] > 0  # type: ignore
        ]

        if len(filtered_key_points) == 0 and not self.allow_general_knowledge:
            # return no data answer if no key points are found
            log.warning(
                "Warning: All map responses have score 0 (i.e., no relevant information found from the dataset), returning a canned 'I do not know' answer. You can try enabling `allow_general_knowledge` to encourage the LLM to incorporate relevant general knowledge, at the risk of increasing hallucinations."
            )
            yield NO_DATA_ANSWER
            return

        filtered_key_points = sorted(
            filtered_key_points,
            key=lambda x: x["score"],  # type: ignore
            reverse=True,  # type: ignore
        )

        data = []
        total_tokens = 0
        for point in filtered_key_points:
            formatted_response_data = [
                f"----Analyst {point['analyst'] + 1}----",
                f"Importance Score: {point['score']}",
                point["answer"],
            ]
            formatted_response_text = "\n".join(formatted_response_data)
            if (
                total_tokens + num_tokens(formatted_response_text, self.token_encoder)
                > self.max_data_tokens
            ):
                break
            data.append(formatted_response_text)
            total_tokens += num_tokens(formatted_response_text, self.token_encoder)
        text_data = "\n\n".join(data)

        search_prompt = self.reduce_system_prompt.format(
            report_data=text_data,
            response_type=self.response_type,
            max_length=max_length,
        )
        if self.allow_general_knowledge:
            search_prompt += "\n" + self.general_knowledge_inclusion_prompt
        search_messages = [
            {"role": "system", "content": search_prompt},
        ]

        async for chunk_response in self.model.achat_stream(
            prompt=query,
            history=search_messages,
            **llm_kwargs,
        ):
            for callback in self.callbacks:
                callback.on_llm_new_token(chunk_response)
            yield chunk_response
