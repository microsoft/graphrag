from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class GraphRAGResponseItem(BaseModel):
    code: int = Field(..., description="The response code")
    message: str = Field(..., description="The response message")
    data: Any = Field(..., description="The response data")
    other: Any = Field(None, description="Other data")


class GraphRAGItem(BaseModel):
    class MethodEnum(str, Enum):
        local = "local"
        global_ = "global"

    class DomainEnum(str, Enum):
        cypnest = "cypnest"

    domain: DomainEnum = Field(..., description="The domain to search")
    question: str = Field(..., description="The query to run")
    method: MethodEnum = Field(MethodEnum.local, description="The method to run, one of: local or global")
    response_type: str = Field("Multiple Paragraphs",
                               description="Free form text describing the response type and format, can be anything, e.g. Multiple Paragraphs, Single Paragraph, Single Sentence, List of 3-7 Points, Single Page, Multi-Page Report")
