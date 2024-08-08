import re

import pandas as pd
from langchain_core.output_parsers import JsonOutputParser

from plugins.webserver import prompt


def delete_reference(text: str) -> str:
    """
    Delete reference from generated text.
    """
    pattern_str = r'\[Data: ((?:Entities|Relationships|Sources|Claims|Reports) \((?:[\d, ]*[^,])(?:, \+more)?\)('r'?:; )?)+\]'
    pattern = re.compile(pattern_str)
    return pattern.sub("", text)


async def get_reference(app_context, context_document_ids: list, question_list: list, llm) -> dict:
    """
    Get reference from context document
    """
    reference = {}
    document = getattr(app_context, "document", None)
    if isinstance(document, pd.DataFrame):
        hit_docs: pd.DataFrame = document[document['id'].isin(context_document_ids)]
        title_link = {row['title']: row['source'] for i, row in hit_docs.iterrows()}
        reference_doc_title_list: list = await get_docs_by_title_filter(str(list(title_link.keys())), str(question_list), llm)

        for idx in reference_doc_title_list:
            try:
                key = list(title_link.keys())[idx]
                link = title_link.get(key)
                reference[key] = link
            except:
                continue

    return reference


async def get_docs_by_title_filter(doc_title_list: str, question: str, llm) -> list:
    """
    Get document title list by filter.
    """
    user_format = """文档标题列表
    {}
    问题
    {}"""

    search_messages = [
        {"role": "system", "content": prompt.best_match_question_prompt},
        {"role": "user", "content": user_format.format(doc_title_list, question)},
    ]

    str_question_list = await llm.agenerate(messages=search_messages, streaming=False, callbacks=None)

    doc_title_list = JsonOutputParser().parse(str_question_list)

    return doc_title_list
