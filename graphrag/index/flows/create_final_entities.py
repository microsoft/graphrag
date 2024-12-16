# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform final entities."""

import pandas as pd


def create_final_entities(
    base_entity_nodes: pd.DataFrame,
) -> pd.DataFrame:
    """All the steps to transform final entities."""
    return base_entity_nodes.loc[
        :,
        [
            "id",
            "human_readable_id",
            "title",
            "type",
            "description",
            "text_unit_ids",
        ],
    ]
