# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Algorithm to rate the relevancy between a query and description text."""

import asyncio
import logging
from contextlib import nullcontext
from typing import TYPE_CHECKING, Any

import numpy as np
from graphrag_llm.tokenizer import Tokenizer
from graphrag_llm.utils import (
    CompletionMessagesBuilder,
    gather_completion_response_async,
)

from graphrag.query.context_builder.rate_prompt import RATE_QUERY
from graphrag.query.llm.text_utils import try_parse_json_object

if TYPE_CHECKING:
    from graphrag_llm.completion import LLMCompletion

logger = logging.getLogger(__name__)


async def rate_relevancy(
    query: str,
    description: str,
    model: "LLMCompletion",
    tokenizer: Tokenizer,
    rate_query: str = RATE_QUERY,
    num_repeats: int = 1,
    semaphore: asyncio.Semaphore | None = None,
    **model_params: Any,
) -> dict[str, Any]:
    """
    Rate the relevancy between the query and description on a scale of 0 to 10.

    Args:
        query: the query (or question) to rate against
        description: the community description to rate, it can be the community
            title, summary, or the full content.
        llm: LLM model to use for rating
        tokenizer: tokenizer
        num_repeats: number of times to repeat the rating process for the same community (default: 1)
        model_params: additional arguments to pass to the LLM model
        semaphore: asyncio.Semaphore to limit the number of concurrent LLM calls (default: None)
    """
    llm_calls, prompt_tokens, output_tokens, ratings = 0, 0, 0, []

    messages_builder = (
        CompletionMessagesBuilder()
        .add_system_message(rate_query.format(description=description, question=query))
        .add_user_message(query)
    )

    for _ in range(num_repeats):
        async with semaphore if semaphore is not None else nullcontext():
            model_response = await model.completion_async(
                messages=messages_builder.build(),
                response_format_json_object=True,
                **model_params,
            )
            response = await gather_completion_response_async(model_response)
        try:
            _, parsed_response = try_parse_json_object(response)
            ratings.append(parsed_response["rating"])
        except KeyError:
            # in case of json parsing error, default to rating 1 so the report is kept.
            # json parsing error should rarely happen.
            logger.warning("Error parsing json response, defaulting to rating 1")
            ratings.append(1)
        llm_calls += 1
        prompt_tokens += tokenizer.num_prompt_tokens(messages_builder.build())
        output_tokens += tokenizer.num_tokens(response)
    # select the decision with the most votes
    options, counts = np.unique(ratings, return_counts=True)
    rating = int(options[np.argmax(counts)])
    return {
        "rating": rating,
        "ratings": ratings,
        "llm_calls": llm_calls,
        "prompt_tokens": prompt_tokens,
        "output_tokens": output_tokens,
    }
