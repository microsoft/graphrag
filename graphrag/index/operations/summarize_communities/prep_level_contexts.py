# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Prepare context for each level of the community hierarchy."""

import pandas as pd

from graphrag.index.operations.summarize_communities.community_reports_extractor import (
    prep_community_report_context,
)
from graphrag.index.operations.summarize_communities.community_reports_extractor.utils import (
    get_levels,
)
from graphrag.index.operations.summarize_communities.restore_community_hierarchy import (
    restore_community_hierarchy,
)


def prep_level_contexts(nodes: pd.DataFrame, local_contexts, max_input_tokens: int):
    """Prepare context for each level of the community hierarchy."""
    community_hierarchy = restore_community_hierarchy(nodes)
    levels = get_levels(nodes)

    level_contexts = []
    for level in levels:
        level_context = prep_community_report_context(
            local_context_df=local_contexts,
            community_hierarchy_df=community_hierarchy,
            level=level,
            max_tokens=max_input_tokens,
        )
        level_contexts.append(level_context)

    return level_contexts
