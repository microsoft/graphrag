# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Algorithm to rate the relevancy between a query and description text."""

import asyncio
import logging
from contextlib import nullcontext
from typing import Any

import numpy as np
import tiktoken

from graphrag.llm.openai.utils import try_parse_json_object
from graphrag.query.context_builder.rate_prompt import RATE_QUERY
from graphrag.query.llm.base import BaseLLM
from graphrag.query.llm.text_utils import num_tokens

log = logging.getLogger(__name__)


async def rate_relevancy(
    query: str,
    description: str,
    llm: BaseLLM,
    token_encoder: tiktoken.Encoding,
    rate_query: str = RATE_QUERY,
    num_repeats: int = 1,
    semaphore: asyncio.Semaphore | None = None,
    **llm_kwargs: Any,
) -> dict[str, Any]:
    """
    Rate the relevancy between the query and description on a scale of 0 to 10.

    Args:
        query: the query (or question) to rate against
        description: the community description to rate, it can be the community
            title, summary, or the full content.
        llm: LLM model to use for rating
        token_encoder: token encoder
        num_repeats: number of times to repeat the rating process for the same community (default: 1)
        llm_kwargs: additional arguments to pass to the LLM model
        semaphore: asyncio.Semaphore to limit the number of concurrent LLM calls (default: None)
    """
    llm_calls, prompt_tokens, output_tokens, ratings = 0, 0, 0, []
    messages = [
        {
            "role": "system",
            "content": rate_query.format(description=description, question=query),
        },
        {"role": "user", "content": query},
    ]
    for _ in range(num_repeats):
        async with semaphore if semaphore is not None else nullcontext():
            response = await llm.agenerate(messages=messages, **llm_kwargs)
        try:
            _, parsed_response = try_parse_json_object(response)
            ratings.append(parsed_response["rating"])
        except KeyError:
            # in case of json parsing error, default to rating 1 so the report is kept.
            # json parsing error should rarely happen.
            log.info("Error parsing json response, defaulting to rating 1")
            ratings.append(1)
        llm_calls += 1
        prompt_tokens += num_tokens(messages[0]["content"], token_encoder)
        output_tokens += num_tokens(response, token_encoder)
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
