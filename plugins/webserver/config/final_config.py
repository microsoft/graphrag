# -*- coding: UTF-8 -*-
"""
@Author : Jarlor Zhang
@Email  : jarlor@foxmail.com
@Date   : 2024/8/7 14:17
@Desc   : 
"""
from pydantic import Field

from graphrag.config import GraphRagConfig
from plugins.webserver.config.query_config import QueryConfig


class FinalConfig(GraphRagConfig):
    query: QueryConfig = Field(description="The query configuration.", default=None)
    """The query configuration."""

    all_index_dir: str = Field(description="The all index directory.", default=None)
