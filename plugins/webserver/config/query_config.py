# -*- coding: UTF-8 -*-
"""
@Author : Jarlor Zhang
@Email  : jarlor@foxmail.com
@Date   : 2024/8/7 14:19
@Desc   : 
"""
from pydantic import BaseModel, Field


class QueryConfig(BaseModel):
    """The reporting configuration."""
    community_level: int = Field(description="The community level to use.", default=2)
    response_type: str = Field(description="The response type to use.", default="Multiple Paragraphs")
