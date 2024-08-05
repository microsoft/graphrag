from graphrag.query.context_builder.builders import LocalContextBuilder
from graphrag.query.llm.base import BaseTextEmbedding


def judge_by_entity_score(context: LocalContextBuilder, question: str, text_embedder: BaseTextEmbedding):
    entity_list = context.entity_text_embeddings.similarity_search_by_text(text=question, text_embedder=lambda t: text_embedder.embed(t), k=20)

    scores = [entity for entity in entity_list]

    return scores