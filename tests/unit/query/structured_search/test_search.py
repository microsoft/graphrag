# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

from unittest.mock import AsyncMock, MagicMock

import pytest

from graphrag.query.context_builder.builders import GlobalContextBuilder
from graphrag.query.llm.base import BaseLLM
from graphrag.query.structured_search.base import SearchResult
from graphrag.query.structured_search.global_search.search import GlobalSearch


class MockLLM(BaseLLM):
    def __init__(self):
        self.call_count = 0
        self.last_messages = None

    def generate(
        self, messages, streaming=False, callbacks=None, max_tokens=None, **kwargs
    ):
        self.call_count += 1
        self.last_messages = messages
        return "mocked response"

    async def agenerate(
        self, messages, streaming=False, callbacks=None, max_tokens=None, **kwargs
    ):
        self.call_count += 1
        self.last_messages = messages
        return "mocked response"


class MockContextBuilder(GlobalContextBuilder):
    def build_context(self, conversation_history=None, **kwargs):
        return ["mocked context"], {}


class TestGlobalSearch(GlobalSearch):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_search_prompt = None

    async def _map_response_single_batch(
        self, context_data: str, query: str, **llm_kwargs
    ):
        search_prompt = self.map_system_prompt.format(context_data=context_data)
        if self.json_mode:
            search_prompt += "\nYour response should be in JSON format."
        self.last_search_prompt = search_prompt
        return await super()._map_response_single_batch(
            context_data, query, **llm_kwargs
        )


@pytest.fixture
def global_search():
    llm = MockLLM()
    context_builder = MockContextBuilder()
    return TestGlobalSearch(llm, context_builder)


@pytest.mark.asyncio
async def test_json_format_instruction_in_search_prompt(global_search):
    global_search.json_mode = True
    query = "Test query"

    global_search.context_builder.build_context = MagicMock(
        return_value=(["mocked context"], {})
    )

    global_search.parse_search_response = MagicMock(
        return_value=[{"answer": "Mocked answer", "score": 100}]
    )

    await global_search.asearch(query)

    assert global_search.last_search_prompt is not None
    assert "Your response should be in JSON format." in global_search.last_search_prompt

    global_search.json_mode = False
    global_search.last_search_prompt = None
    await global_search.asearch(query)

    assert global_search.last_search_prompt is not None
    assert (
        "Your response should be in JSON format."
        not in global_search.last_search_prompt
    )


def test_parse_search_response_valid(global_search):
    valid_response = """
    {
        "points": [
            {"description": "Point 1", "score": 90},
            {"description": "Point 2", "score": 80}
        ]
    }
    """
    result = global_search.parse_search_response(valid_response)
    assert len(result) == 2
    assert result[0] == {"answer": "Point 1", "score": 90}
    assert result[1] == {"answer": "Point 2", "score": 80}


def test_parse_search_response_invalid_json(global_search):
    invalid_json = "This is not JSON"
    with pytest.raises(ValueError, match="Failed to parse response as JSON"):
        global_search.parse_search_response(invalid_json)


def test_parse_search_response_missing_points(global_search):
    missing_points = '{"data": "No points here"}'
    with pytest.raises(
        ValueError, match="Response JSON does not contain a 'points' list"
    ):
        global_search.parse_search_response(missing_points)


def test_parse_search_response_invalid_point_format(global_search):
    invalid_point = """
    {
        "points": [
            {"wrong_key": "Point 1", "score": 90}
        ]
    }
    """
    with pytest.raises(ValueError, match="Error processing points"):
        global_search.parse_search_response(invalid_point)


def test_parse_search_response_non_integer_score(global_search):
    non_integer_score = """
    {
        "points": [
            {"description": "Point 1", "score": "high"}
        ]
    }
    """
    with pytest.raises(ValueError, match="Error processing points"):
        global_search.parse_search_response(non_integer_score)


@pytest.mark.asyncio
async def test_map_response(global_search):
    global_search.map_response = AsyncMock(
        return_value=[
            SearchResult(
                response=[{"answer": "Test answer", "score": 90}],
                context_data="Test context",
                context_text="Test context",
                completion_time=0.1,
                llm_calls=1,
                prompt_tokens=10,
            )
        ]
    )

    context_data = ["Test context"]
    query = "Test query"
    result = await global_search.map_response(context_data, query)

    assert isinstance(result[0], SearchResult)
    assert result[0].context_data == "Test context"
    assert result[0].context_text == "Test context"
    assert result[0].llm_calls == 1


@pytest.mark.asyncio
async def test_reduce_response(global_search):
    global_search.reduce_response = AsyncMock(
        return_value=SearchResult(
            response="Final answer",
            context_data="Combined context",
            context_text="Combined context",
            completion_time=0.2,
            llm_calls=1,
            prompt_tokens=20,
        )
    )

    map_responses = [
        SearchResult(
            response=[{"answer": "Point 1", "score": 90}],
            context_data="",
            context_text="",
            completion_time=0,
            llm_calls=1,
            prompt_tokens=0,
        ),
        SearchResult(
            response=[{"answer": "Point 2", "score": 80}],
            context_data="",
            context_text="",
            completion_time=0,
            llm_calls=1,
            prompt_tokens=0,
        ),
    ]
    query = "Test query"
    result = await global_search.reduce_response(map_responses, query)

    assert isinstance(result, SearchResult)
    assert result.llm_calls == 1
    assert result.response == "Final answer"
