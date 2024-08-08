from typing import Union

from graphrag.query.context_builder.builders import GlobalContextBuilder, LocalContextBuilder

ContextBuilder = Union[LocalContextBuilder, GlobalContextBuilder]