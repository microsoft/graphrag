import tiktoken
import numpy as np
from typing import Dict, Any

from graphrag.query.llm.oai.chat_openai import ChatOpenAI

RATE_QUERY = """
You are a helpful assistant responsible for deciding whether the provided information 
is useful in answering a given question, even if it is only partially relevant.

On a scale from 1 to 5, please rate how relevant or helpful is the provided information in answering the question:
1 - Not relevant in any way to the question
2 - Potentially relevant to the question
3 - Relevant to the question
4 - Highly relevant to the question
5 - It directly answers to the question


#######
Information
{description}
######
Question
{question}
######
Please only return the rating value.
"""


async def rate_relevancy(
    query: str,
    description: str,
    llm: ChatOpenAI,
    token_encoder: tiktoken.Encoding,
    num_repeats: int = 1,
    **llm_kwargs: Any
) -> Dict[str, Any]:
    """
    Rate the relevancy between the query and description on a scale of 1 to 5.
    A rating of 1 indicates the community is not relevant to the query and a rating of 5
    indicates the community directly answers the query.

    Args:
        query: the query (or question) to rate against
        description: the community description to rate, it can be the community
            title, summary, or the full content.
    Returns:
        result: a dictionary containing
            rating: the relevancy rating between the query and description.
                In the case of multiple repeats, the rating wit h the most vote is selected.
            ratings: list of ratings of size num_repeats
            llm_calls: number of calls to LLM
            prompt_tokens: number of tokens used in the LLM calls
    """
    llm_calls, prompt_tokens, ratings = 0, 0, []
    messages = [
        {
            "role": "system",
            "content": RATE_QUERY.format(description=description, question=query),
        },
        {"role": "user", "content": query},
    ]
    for repeat in range(num_repeats):
        response = await llm.agenerate(messages=messages, **llm_kwargs)
        ratings.append(int(response[0]))
        llm_calls += 1
        prompt_tokens += len(token_encoder.encode(messages[0]["content"]))
        prompt_tokens += len(token_encoder.encode(messages[1]["content"]))
    # select the decision with the most votes
    options, counts = np.unique(ratings, return_counts=True)
    rating = options[np.argmax(counts)]
    return {
        "rating": rating,
        "ratings": ratings,
        "llm_calls": llm_calls,
        "prompt_tokens": prompt_tokens,
    }
