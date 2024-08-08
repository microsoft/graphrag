import asyncio
from typing import Optional, Generator
from openai.types import CompletionUsage
from fastapi.responses import StreamingResponse

from graphrag.query.context_builder.conversation_history import ConversationHistory
from graphrag.query.llm.base import BaseLLMCallback
from graphrag.query.structured_search.base import BaseSearch, SearchResult
from plugins.webserver.types import TypedFuture, GraphRAGItem, GraphRAGResponseItem


async def handle_stream_response(question_list: list, reference: dict, search: BaseSearch, conversation_history: ConversationHistory):
    callback = CustomSearchCallback()
    future = TypedFuture[SearchResult]()

    async def run_search():
        result = await search.asearch(str(question_list), conversation_history)
        future.set_result(result)

    search.callbacks = [callback]
    asyncio.create_task(run_search())
    return StreamingResponse(generate_chunks(callback, future, reference, question_list), media_type="text/event-stream")


class SearchLLMCallback(BaseLLMCallback):
    """Search LLM Callbacks."""

    def __init__(self):
        super().__init__()
        self.map_response_contexts = []
        self.map_response_outputs = []

    def on_map_response_start(self, map_response_contexts: list[str]):
        """Handle the start of map response."""
        self.map_response_contexts = map_response_contexts

    def on_map_response_end(self, map_response_outputs: list[SearchResult]):
        """Handle the end of map response."""
        self.map_response_outputs = map_response_outputs


class CustomSearchCallback(SearchLLMCallback):
    stop_sign = '<<STOP>><<停止>>🅿️<<STOP>><<停止>>'

    def __init__(self):
        super().__init__()
        self.token_queue = asyncio.Queue()
        self.usage: Optional[CompletionUsage] = None

    def on_map_response_start(self, map_response_contexts: list[str]):
        super().on_map_response_start(map_response_contexts)
        return map_response_contexts

    def on_map_response_end(self, map_response_outputs: list[SearchResult]):
        super().on_map_response_end(map_response_outputs)
        return map_response_outputs

    def on_llm_new_token(self, token: str):
        """Synchronous method to handle new tokens."""
        super().on_llm_new_token(token)
        asyncio.create_task(self.async_on_llm_new_token(token))  # Schedule async method

    def on_llm_stop(self, usage: CompletionUsage):
        super().on_llm_stop(usage)
        self.usage = usage
        asyncio.create_task(self.async_on_llm_new_token(CustomSearchCallback.stop_sign))  # Schedule async method

    async def async_on_llm_new_token(self, token: str):
        """Asynchronous version to handle new tokens."""
        await self.token_queue.put(token)

    async def generate_tokens(self) -> Generator[str, None, None]:
        while True:
            token = await self.token_queue.get()
            yield token
            if token == CustomSearchCallback.stop_sign:
                break


async def generate_chunks(callback, future: TypedFuture[SearchResult], reference, question_list):
    while not future.done():
        all_response = ''
        async for token in callback.generate_tokens():
            all_response += token
            if token == CustomSearchCallback.stop_sign:
                break
            chunk = GraphRAGResponseItem(
                code=200,
                message="success",
                reference=reference,
                data=token,
                question=question_list,
                other={"usage": callback.usage, "all_response": all_response}
            )
            yield f"data: {chunk.json()}\n\n"

    yield f"data: [DONE]\n\n"
