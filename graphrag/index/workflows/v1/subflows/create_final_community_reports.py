# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform community reports."""

from typing import cast

import pandas as pd
from datashaper import (
    Table,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result


@verb(name="create_final_community_reports", treats_input_tables_as_immutable=True)
def create_final_community_reports(
    input: VerbInput,
    document_attribute_columns: list[str] | None = None,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform community reports."""
    source = cast(pd.DataFrame, input.get_input())

    return create_verb_result(
        cast(
            Table,
            source,
        )
    )
