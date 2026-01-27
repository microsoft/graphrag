# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final entities."""

from uuid import uuid4

import pandas as pd

from graphrag.data_model.schemas import ENTITIES_FINAL_COLUMNS
from graphrag.index.operations.compute_degree import compute_degree
from graphrag.index.operations.create_graph import create_graph


def finalize_entities(
    entities: pd.DataFrame,
    relationships: pd.DataFrame,
) -> pd.DataFrame:
    """All the steps to transform final entities."""
    graph = create_graph(relationships, edge_attr=["weight"])
    degrees = compute_degree(graph)
    final_entities = entities.merge(degrees, on="title", how="left").drop_duplicates(
        subset="title"
    )
    final_entities = final_entities.loc[entities["title"].notna()].reset_index()
    # disconnected nodes and those with no community even at level 0 can be missing degree
    final_entities["degree"] = final_entities["degree"].fillna(0).astype(int)
    final_entities.reset_index(inplace=True)
    final_entities["human_readable_id"] = final_entities.index
    final_entities["id"] = final_entities["human_readable_id"].apply(
        lambda _x: str(uuid4())
    )
    return final_entities.loc[
        :,
        ENTITIES_FINAL_COLUMNS,
    ]
