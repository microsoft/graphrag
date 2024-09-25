# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Algorithm to dynamically select relevant communities with respect to a query."""

import asyncio
import logging
from collections import Counter
from copy import deepcopy
from time import time
import tiktoken

from graphrag.model import Community, CommunityReport
from graphrag.query.context_builder.rate_relevancy import rate_relevancy
from graphrag.query.llm.oai.chat_openai import ChatOpenAI

log = logging.getLogger(__name__)


class DynamicCommunitySelection:
    """Dynamic community selection to select community reports that are relevant to the query."""

    def __init__(
        self,
        community_reports: list[CommunityReport],
        communities: list[Community],
        llm: ChatOpenAI,
        token_encoder: tiktoken.Encoding,
        keep_parent: bool = False,
        num_repeats: int = 1,
        use_logit_bias: bool = True,
        concurrent_coroutines: int = 4,
    ):
        self.community_reports = {
            report.community_id: report for report in community_reports
        }
        # mapping from community to sub communities
        self.node2children = {
            community.id: set(community.sub_community_ids) for community in communities
        }
        # mapping from community to parent community
        self.node2parent = {
            sub_community: community
            for community, sub_communities in self.node2children.items()
            for sub_community in sub_communities
        }
        # get all communities at level 0
        self.root_communities = [
            community.id
            for community in communities
            if community.level == "0" and community.id in self.community_reports
        ]
        self.llm = llm
        self.token_encoder = token_encoder
        self.keep_parent = keep_parent
        self.num_repeats = num_repeats
        self.llm_kwargs = {"temperature": 0.0, "max_tokens": 2}
        if use_logit_bias:
            # bias the output to the rating tokens
            self.llm_kwargs["logit_bias"] = {
                token_encoder.encode(token)[0]: 5 for token in ["1", "2", "3", "4", "5"]
            }
        self.semaphore = asyncio.Semaphore(concurrent_coroutines)

    async def select(self, query: str) -> tuple[list[CommunityReport], int, int]:
        """
        Select relevant communities with respect to the query.

        Args:
            query: the query to rate against
        """
        start = time()
        queue = deepcopy(self.root_communities)  # start search from level 0 communities

        ratings = []  # store the ratings for each community
        llm_calls, prompt_tokens = 0, 0
        relevant_communities = set()
        while queue:
            gather_results = await asyncio.gather(
                *[
                    rate_relevancy(
                        query=query,
                        description=self.community_reports[community].summary,
                        llm=self.llm,
                        token_encoder=self.token_encoder,
                        num_repeats=self.num_repeats,
                        semaphore=self.semaphore,
                        **self.llm_kwargs,
                    )
                    for community in queue
                ]
            )

            communities_to_rate = []
            for community, result in zip(queue, gather_results, strict=True):
                rating = result["rating"]
                ratings.append(rating)
                llm_calls += result["llm_calls"]
                prompt_tokens += result["prompt_tokens"]
                if rating > 1:
                    relevant_communities.add(community)
                    # find children nodes of the current node and append them to the queue
                    # TODO check why some sub_communities are NOT in report_df
                    if community in self.node2children:
                        communities_to_rate.extend(
                            [
                                sub_community
                                for sub_community in self.node2children[community]
                                if sub_community in self.community_reports
                            ]
                        )
                    # remove parent node if the current node is deemed relevant
                    if not self.keep_parent and community in self.node2parent:
                        relevant_communities.discard(self.node2parent[community])
            queue = communities_to_rate

        community_reports = [
            self.community_reports[community] for community in relevant_communities
        ]
        end = time()

        log.info(
            "Dynamic community selection (took: {0:.0f}s)\n"
            "\trating distribution {1}\n"
            "\t{2} out of {3} community reports are relevant".format(
                end - start,
                dict(sorted(Counter(ratings).items())),
                len(relevant_communities),
                len(self.community_reports),
            )
        )

        return community_reports, llm_calls, prompt_tokens
