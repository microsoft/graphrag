import logging
from contextlib import asynccontextmanager
from pathlib import Path

import pandas as pd
import tiktoken
from fastapi import FastAPI, HTTPException

from graphrag.query.llm.oai import ChatOpenAI, OpenAIEmbedding
from graphrag.query.structured_search.global_search.search import GlobalSearch
from graphrag.query.structured_search.local_search.search import LocalSearch
from plugins.webserver import utils
from plugins.webserver.models import GraphRAGItem, GraphRAGResponseItem
from plugins.context2question import utils as c2q_utils
from plugins.webserver.settings import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# global variables
llm: ChatOpenAI
text_embedder: OpenAIEmbedding
local_search: LocalSearch
global_search: GlobalSearch
token_encoder: tiktoken.Encoding
all_contexts = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm, text_embedder, local_search, global_search, token_encoder, all_contexts
    llm, text_embedder, local_search, global_search, token_encoder, all_contexts = await utils.init_env()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/graphrag", response_model=GraphRAGResponseItem)
async def graphrag(request: GraphRAGItem):
    if not local_search or not global_search:
        logger.error("graphrag search engines is not initialized")
        raise HTTPException(status_code=500, detail="graphrag search engines is not initialized")

    # switch context via domain
    context = await utils.switch_context(request.domain, request.method.value, all_contexts)

    try:
        # generate answer from user chat context
        generate_question_list = await c2q_utils.context_to_question(user_context=request.question, llm=llm)
    except Exception:
        return GraphRAGResponseItem(code=200, message="refuse answer", question=[], data=None, user_context=request.question)
    question_list, context_document_ids = c2q_utils.filter_question_by_bm25(generate_question_list, context)

    # get reference
    reference = {}
    document = getattr(context, "document", None)
    if isinstance(document, pd.DataFrame):
        hit_docs: pd.DataFrame = document[document['id'].isin(context_document_ids)]
        title_link = {row['source']: row['title'] for i, row in hit_docs.iterrows()}
        reference_doc_title_list: list = await c2q_utils.get_docs_by_title_filter(str(list(title_link.keys())), str(question_list), llm)

        for idx in reference_doc_title_list:
            try:
                key = list(title_link.keys())[idx]
                link = title_link.get(key)
                reference[key] = link
            except:
                continue

    if request.method == GraphRAGItem.MethodEnum.global_:
        global_search.context_builder = context
        result = await global_search.asearch('\n'.join(question_list))
    else:
        local_search.context_builder = context
        result = await local_search.asearch('\n'.join(question_list))

    ori_response = result.response
    response = utils.delete_reference(ori_response)
    return GraphRAGResponseItem(code=200, message="success", question=question_list, data=response, user_context=request.question,
                                other={"ori_response": result.response, "context": result.context_text}, reference=reference)


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
