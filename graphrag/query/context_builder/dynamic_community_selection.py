# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Algorithm to dynamically select relevant communities with respect to a query."""

import asyncio
import logging
from collections import Counter
from copy import deepcopy
from time import time
from typing import Any

import tiktoken

from graphrag.data_model.community import Community
from graphrag.data_model.community_report import CommunityReport
from graphrag.language_model.protocol.base import ChatModel
from graphrag.query.context_builder.rate_prompt import RATE_QUERY
from graphrag.query.context_builder.rate_relevancy import rate_relevancy

log = logging.getLogger(__name__)


class DynamicCommunitySelection:
    """Dynamic community selection to select community reports that are relevant to the query.

    Any community report with a rating EQUAL or ABOVE the rating_threshold is considered relevant.
    """

    def __init__(
        self,
        community_reports: list[CommunityReport],
        communities: list[Community],
        model: ChatModel,
        token_encoder: tiktoken.Encoding,
        rate_query: str = RATE_QUERY,
        use_summary: bool = False,
        threshold: int = 1,
        keep_parent: bool = False,
        num_repeats: int = 1,
        max_level: int = 2,
        concurrent_coroutines: int = 8,
        model_params: dict[str, Any] | None = None,
    ):
        self.model = model
        self.token_encoder = token_encoder
        self.rate_query = rate_query
        self.num_repeats = num_repeats
        self.use_summary = use_summary
        self.threshold = threshold
        self.keep_parent = keep_parent
        self.max_level = max_level
        self.semaphore = asyncio.Semaphore(concurrent_coroutines)
        self.model_params = model_params if model_params else {}

        self.reports = {report.community_id: report for report in community_reports}
        self.communities = {community.short_id: community for community in communities}

        # mapping from level to communities
        self.levels: dict[str, list[str]] = {}

        for community in communities:
            if community.level not in self.levels:
                self.levels[community.level] = []
            if community.short_id in self.reports:
                self.levels[community.level].append(community.short_id)

        # start from root communities (level 0)
        self.starting_communities = self.levels["0"]

    async def select(self, query: str) -> tuple[list[CommunityReport], dict[str, Any]]:
        """
        Select relevant communities with respect to the query.

        Args:
            query: the query to rate against
        """
        start = time()
        queue = deepcopy(self.starting_communities)
        level = 0

        ratings = {}  # store the ratings for each community
        llm_info: dict[str, Any] = {
            "llm_calls": 0,
            "prompt_tokens": 0,
            "output_tokens": 0,
        }
        relevant_communities = set()

        while queue:
            gather_results = await asyncio.gather(*[
                rate_relevancy(
                    query=query,
                    description=(
                        self.reports[community].summary
                        if self.use_summary
                        else self.reports[community].full_content
                    ),
                    model=self.model,
                    token_encoder=self.token_encoder,
                    rate_query=self.rate_query,
                    num_repeats=self.num_repeats,
                    semaphore=self.semaphore,
                    **self.model_params,
                )
                for community in queue
            ])

            communities_to_rate = []
            for community, result in zip(queue, gather_results, strict=True):
                rating = result["rating"]
                log.debug(
                    "dynamic community selection: community %s rating %s",
                    community,
                    rating,
                )
                ratings[community] = rating
                llm_info["llm_calls"] += result["llm_calls"]
                llm_info["prompt_tokens"] += result["prompt_tokens"]
                llm_info["output_tokens"] += result["output_tokens"]
                if rating >= self.threshold:
                    relevant_communities.add(community)
                    # find children nodes of the current node and append them to the queue
                    # TODO check why some sub_communities are NOT in report_df
                    if community in self.communities:
                        for child in self.communities[community].children:
                            if child in self.reports:
                                communities_to_rate.append(child)
                            else:
                                log.debug(
                                    "dynamic community selection: cannot find community %s in reports",
                                    child,
                                )
                    # remove parent node if the current node is deemed relevant
                    if not self.keep_parent and community in self.communities:
                        relevant_communities.discard(self.communities[community].parent)
            queue = communities_to_rate
            level += 1
            if (
                (len(queue) == 0)
                and (len(relevant_communities) == 0)
                and (str(level) in self.levels)
                and (level <= self.max_level)
            ):
                log.info(
                    "dynamic community selection: no relevant community "
                    "reports, adding all reports at level %s to rate.",
                    level,
                )
                # append all communities at the next level to queue
                queue = self.levels[str(level)]

        community_reports = [
            self.reports[community] for community in relevant_communities
        ]
        end = time()

        log.info(
            "dynamic community selection (took: %ss)\n"
            "\trating distribution %s\n"
            "\t%s out of %s community reports are relevant\n"
            "\tprompt tokens: %s, output tokens: %s",
            int(end - start),
            dict(sorted(Counter(ratings.values()).items())),
            len(relevant_communities),
            len(self.reports),
            llm_info["prompt_tokens"],
            llm_info["output_tokens"],
        )

        llm_info["ratings"] = ratings
        return community_reports, llm_info
