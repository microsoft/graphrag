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

from graphrag.config import GraphRagConfig
from graphrag.model import Community, CommunityReport
from graphrag.query.context_builder.rate_relevancy import rate_relevancy
from graphrag.query.llm.get_llm import get_llm

log = logging.getLogger(__name__)


class DynamicCommunitySelection:
    """Dynamic community selection to select community reports that are relevant to the query.
    Any community report with a rating EQUAL or ABOVE the rating_threshold is considered relevant.
    """

    def __init__(
        self,
        config: GraphRagConfig,
        community_reports: list[CommunityReport],
        communities: list[Community],
    ):
        self.reports = {report.community_id: report for report in community_reports}
        # mapping from community to sub communities
        self.node2children = {
            community.id: (
                []
                if community.sub_community_ids is None
                else community.sub_community_ids
            )
            for community in communities
        }
        # mapping from community to parent community
        self.node2parent: dict[str, str] = {
            sub_community: community
            for community, sub_communities in self.node2children.items()
            for sub_community in sub_communities
        }
        # mapping from level to communities
        self.levels: dict[str, list[str]] = {}
        for community in communities:
            if community.level not in self.levels:
                self.levels[community.level] = []
            if community.id in self.reports:
                self.levels[community.level].append(community.id)

        # start from root communities (level 0)
        self.starting_communities = self.levels["0"]

        # create LLM dedicated for dynamic community selection
        gs_config = config.global_search
        _config = deepcopy(config)
        _config.llm.model = _config.llm.deployment_name = gs_config.dynamic_search_llm
        self.llm = get_llm(_config)
        self.token_encoder = tiktoken.encoding_for_model(self.llm.model)
        self.keep_parent = gs_config.dynamic_search_keep_parent
        self.num_repeats = gs_config.dynamic_search_num_repeats
        self.use_summary = gs_config.dynamic_search_use_summary
        self.llm_kwargs = {"temperature": 0.0, "max_tokens": 2000}
        self.semaphore = asyncio.Semaphore(
            gs_config.dynamic_search_concurrent_coroutines
        )
        self.threshold = gs_config.dynamic_search_threshold
        self.max_level = gs_config.dynamic_search_max_level

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
        llm_info = {"llm_calls": 0, "prompt_tokens": 0, "output_tokens": 0}
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
                    llm=self.llm,
                    token_encoder=self.token_encoder,
                    num_repeats=self.num_repeats,
                    semaphore=self.semaphore,
                    **self.llm_kwargs,
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
                    if community in self.node2children:
                        for sub_community in self.node2children[community]:
                            if sub_community in self.reports:
                                communities_to_rate.append(sub_community)
                            else:
                                log.debug(
                                    "dynamic community selection: cannot find community %s in reports",
                                    sub_community,
                                )
                    # remove parent node if the current node is deemed relevant
                    if not self.keep_parent and community in self.node2parent:
                        relevant_communities.discard(self.node2parent[community])
            queue = communities_to_rate
            level += 1
            if (
                len(queue) == 0
                and len(relevant_communities) == 0
                and str(level) in self.levels
            ):
                if level <= self.max_level:
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
