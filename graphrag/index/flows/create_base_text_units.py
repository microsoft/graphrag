# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""All the steps to transform base text_units."""

from typing import cast

import pandas as pd

from graphrag.callbacks.workflow_callbacks import WorkflowCallbacks
from graphrag.config.models.chunking_config import ChunkStrategyType
from graphrag.index.operations.chunk_text.chunk_text import chunk_text
from graphrag.index.utils.hashing import gen_sha512_hash
from graphrag.logger.progress import Progress


def create_base_text_units(
    documents: pd.DataFrame,
    callbacks: WorkflowCallbacks,
    group_by_columns: list[str],
    size: int,
    overlap: int,
    encoding_model: str,
    strategy: ChunkStrategyType,
    metadata: list[str] | None,
    line_delimiter: str = ".\n",
) -> pd.DataFrame:
    """All the steps to transform base text_units."""
    sort = documents.sort_values(by=["id"], ascending=[True])

    sort["text_with_ids"] = list(
        zip(*[sort[col] for col in ["id", "text"]], strict=True)
    )

    callbacks.progress(Progress(percent=0))

    agg_dict = {"text_with_ids": list}
    if metadata:
        for meta in metadata:
            agg_dict[meta] = "first"  # type: ignore

    aggregated = (
        (
            sort.groupby(group_by_columns, sort=False)
            if len(group_by_columns) > 0
            else sort.groupby(lambda _x: True)
        )
        .agg(agg_dict)
        .reset_index()
    )  # in here I need to add the metadata columns to it

    aggregated.rename(columns={"text_with_ids": "texts"}, inplace=True)

    aggregated["chunks"] = chunk_text(
        aggregated,
        column="texts",
        size=size,
        overlap=overlap,
        encoding_model=encoding_model,
        strategy=strategy,
        callbacks=callbacks,
        metadata=metadata or [],
        line_delimiter=line_delimiter,
    )

    aggregated = cast("pd.DataFrame", aggregated[[*group_by_columns, "chunks"]])
    aggregated = aggregated.explode("chunks")
    aggregated.rename(
        columns={
            "chunks": "chunk",
        },
        inplace=True,
    )
    aggregated["id"] = aggregated.apply(
        lambda row: gen_sha512_hash(row, ["chunk"]), axis=1
    )
    aggregated[["document_ids", "chunk", "n_tokens"]] = pd.DataFrame(
        aggregated["chunk"].tolist(), index=aggregated.index
    )
    # rename for downstream consumption
    aggregated.rename(columns={"chunk": "text"}, inplace=True)

    return cast(
        "pd.DataFrame", aggregated[aggregated["text"].notna()].reset_index(drop=True)
    )
