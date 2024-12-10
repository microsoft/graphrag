# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing build_steps method definition."""

from typing import TYPE_CHECKING, cast

from datashaper import (
    DEFAULT_INPUT_NAME,
    Table,
    VerbInput,
    verb,
)
from datashaper.table_store.types import VerbResult, create_verb_result

from graphrag.index.config.workflow import PipelineWorkflowConfig, PipelineWorkflowStep
from graphrag.index.flows.create_final_documents import (
    create_final_documents as create_final_documents_flow,
)
from graphrag.storage.pipeline_storage import PipelineStorage

if TYPE_CHECKING:
    import pandas as pd


workflow_name = "create_final_documents"


def build_steps(
    config: PipelineWorkflowConfig,
) -> list[PipelineWorkflowStep]:
    """
    Create the final documents table.

    ## Dependencies
    * `workflow:create_base_text_units`
    """
    document_attribute_columns = config.get("document_attribute_columns", None)
    return [
        {
            "verb": "create_final_documents",
            "args": {"document_attribute_columns": document_attribute_columns},
            "input": {
                "source": DEFAULT_INPUT_NAME,
                "text_units": "workflow:create_base_text_units",
            },
        },
    ]


@verb(
    name="create_final_documents",
    treats_input_tables_as_immutable=True,
)
async def create_final_documents(
    input: VerbInput,
    runtime_storage: PipelineStorage,
    document_attribute_columns: list[str] | None = None,
    **_kwargs: dict,
) -> VerbResult:
    """All the steps to transform final documents."""
    source = cast("pd.DataFrame", input.get_input())
    text_units = await runtime_storage.get("base_text_units")

    output = create_final_documents_flow(source, text_units, document_attribute_columns)

    return create_verb_result(cast("Table", output))
