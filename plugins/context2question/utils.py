# -*- coding: UTF-8 -*-
"""
@Author : Jarlor Zhang
@Email  : jarlor@foxmail.com
@Date   : 2024/8/2 19:04
@Desc   : 
"""
from langchain_core.output_parsers import JsonOutputParser

from plugins.context2question import prompt
import numpy as np
from typing import List
from rank_bm25 import BM25Okapi
import jieba
from tenacity import retry, stop_after_attempt, wait_fixed


@retry(stop=stop_after_attempt(3), wait=wait_fixed(1), reraise=True)
async def context_to_question(user_context: list, llm, app_context) -> list:
    """
    Generate a question based on the user context

    Args:
        user_context: The context provided by the user chat
        llm: The language model to generate the question

    Returns:
        list: The generated question
    """
    search_messages = [
        {"role": "system", "content": prompt.summary_question_prompt},
        {"role": "user", "content": str(user_context)},
    ]

    str_question_list = await llm.agenerate(messages=search_messages, streaming=False, callbacks=None)

    question_list = JsonOutputParser().parse(str_question_list)
    if not question_list:
        raise Exception("No question generated")

    final_question_list = []
    for __ in question_list:
        result_contex = app_context.build_context(__)
        context_sources = result_contex[1].get('sources')['text'].tolist()
        best_score = get_bm25_top_n_score(__, context_sources, n=1)
        if best_score[0] > 0:
            final_question_list.append(__)

    return final_question_list


def get_bm25_top_n_score(question: str, context: List[str], n: int = 1) -> List[float]:
    """
    Calculate the BM25 score of the question and context

    Args:
        question: The question to be asked
        context: The context to be searched
        n: The number of top scores to return
    Returns:
        List[float]: The top n BM25 scores
    """
    if not context:
        return [-1]

    tokenized_question = jieba.lcut(question)
    tokenized_context = [jieba.lcut(_) for _ in context]

    bm25 = BM25Okapi(tokenized_context, k1=1.2)
    scores = bm25.get_scores(tokenized_question)
    return np.sort(scores)[::-1][:n].tolist()
