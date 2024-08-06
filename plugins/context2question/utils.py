# -*- coding: UTF-8 -*-
"""
@Author : Jarlor Zhang
@Email  : jarlor@foxmail.com
@Date   : 2024/8/2 19:04
@Desc   : 
"""
from collections import Counter

import pandas as pd
from langchain_core.output_parsers import JsonOutputParser

from plugins.context2question import prompt
import numpy as np
from typing import List
from rank_bm25 import BM25Okapi
import jieba
from tenacity import retry, stop_after_attempt, wait_fixed

from plugins.webserver import consts


@retry(stop=stop_after_attempt(3), wait=wait_fixed(1), reraise=True)
async def context_to_question(user_context: list, llm) -> list:
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

    return question_list


def filter_question_by_bm25(question_list: list, app_context, threshold: float = 0.0) -> tuple:
    """
    Filter the question list based on the BM25 score

    Args:
        question_list: The list of questions to be filtered
        app_context: The context of the application
        threshold: The threshold to filter the question list

    Returns:
        List[str]: The filtered question
        List[str]: The context document ids
    """
    final_question_list = []
    final_document_ids = []
    for __ in question_list:
        result_contex = app_context.build_context(__)
        context_document_ids = result_contex[1].get('sources')['document_ids'].apply(lambda x: x.split(','))

        context_sources = result_contex[1].get('sources')['text'].tolist()
        context_sources = [_ for _ in context_sources if type(_) == str]
        best_score = get_bm25_top_n_score(__, context_sources, n=1)
        if best_score[0] > threshold:
            final_question_list.append(__)
            final_document_ids.extend(context_document_ids.sum())

    return final_question_list, final_document_ids


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


async def get_docs_by_title_filter(doc_title_list: str, question: str, llm) -> list:
    format = """文档标题列表
    {}
    问题
    {}"""

    search_messages = [
        {"role": "system", "content": prompt.best_match_question_prompt},
        {"role": "user", "content": format.format(doc_title_list, question)},
    ]

    str_question_list = await llm.agenerate(messages=search_messages, streaming=False, callbacks=None)

    doc_title_list = JsonOutputParser().parse(str_question_list)

    return doc_title_list
