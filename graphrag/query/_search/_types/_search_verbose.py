# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License.

from __future__ import annotations

import typing

from . import _search


class SearchResultVerbose(_search.SearchResult):
    context_data: typing.Optional[typing.Union[str, typing.List[typing.Any], typing.Dict[str, typing.Any]]] = None

    context_text: typing.Optional[typing.Union[str, typing.List[str], typing.Dict[str, str]]] = None

    completion_time: float

    llm_calls: int

    map_result: typing.Optional[typing.List[_search.SearchResult]] = None

    reduce_context_data: typing.Optional[
        typing.Union[str, typing.List[typing.Any], typing.Dict[str, typing.Any]]
    ] = None

    reduce_context_text: typing.Optional[typing.Union[str, typing.List[str], typing.Dict[str, str]]] = None
