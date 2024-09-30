# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to extract and format covariates."""

from typing import Any, cast
from uuid import uuid4

import pandas as pd
from datashaper import (
    AsyncType,
    Table,
    VerbCallbacks,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.cache import PipelineCache


@verb(name="create_base_extracted_entities", treats_input_tables_as_immutable=True)
async def create_base_extracted_entities(
    input: VerbInput,
    cache: PipelineCache,
    callbacks: VerbCallbacks,
    **kwargs: dict,
) -> VerbResult:
    """All the steps to extract and format covariates."""
    source = cast(pd.DataFrame, input.get_input())

    
    return create_verb_result(
        cast(
            Table,
            source
        )
    )
