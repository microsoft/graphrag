# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Explode a list of communities into nodes for filtering."""

import pandas as pd

from graphrag.data_model.schemas import (
    COMMUNITY_ID,
)


def explode_communities(
    communities: pd.DataFrame, entities: pd.DataFrame
) -> pd.DataFrame:
    """Explode a list of communities into nodes for filtering."""
    community_join = communities.explode("entity_ids").loc[
        :, ["community", "level", "entity_ids"]
    ]
    nodes = entities.merge(
        community_join, left_on="id", right_on="entity_ids", how="left"
    )
    return nodes.loc[nodes.loc[:, COMMUNITY_ID] != -1]
