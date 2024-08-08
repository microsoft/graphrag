import asyncio
from typing import List, Dict, Any

from pydantic import BaseModel, Field

from plugins.webserver.types import DomainEnum, SearchModeEnum, SourceEnum


class ChatCompletionMessageParam(BaseModel):
    content: str
    role: str = "user"


class ResponseFormat(BaseModel):
    type: str


class ChatCompletionToolParam(BaseModel):
    name: str
    description: str


class GraphRAGItem(BaseModel):
    domain: DomainEnum = Field(..., description="The domain to search_engine")
    method: SearchModeEnum = Field(SearchModeEnum.local, description="The method to run, one of: local or global")
    messages: List[ChatCompletionMessageParam] = Field(..., description="The chat messages")
    stream: bool = Field(False, description="The stream mode")
    response_type: str = Field("Multiple Paragraphs",
                               description="Free form text describing the response type and format, can be anything, e.g. Multiple Paragraphs, "
                                           "Single Paragraph, Single Sentence, List of 3-7 Points, Single Page, Multi-Page Report")
    source: SourceEnum = Field(SourceEnum.qa, description="The source of the request")


class GraphRAGResponseItem(BaseModel):
    code: int = Field(..., description="The response code")
    message: str = Field(..., description="The response message")
    reference: Dict[str, Any] = Field(..., description="The response reference")
    question: List = Field(..., description="The generated question")
    data: Any = Field(..., description="The response data")
    other: Any = Field(None, description="Other data")


class TypedFuture(asyncio.Future):
    pass
