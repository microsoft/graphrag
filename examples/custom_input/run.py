# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import asyncio
import os

import pandas as pd

from graphrag.index import run_pipeline_with_config

pipeline_file = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "./pipeline.yml"
)


async def run():
    # Load your dataset
    dataset = _load_dataset_some_unique_way()

    # Load your config without the input section
    config = pipeline_file

    # Grab the last result from the pipeline, should be our entity extraction
    outputs = []
    async for output in run_pipeline_with_config(
        config_or_path=config, dataset=dataset
    ):
        outputs.append(output)
    pipeline_result = outputs[-1]

    if pipeline_result.result is not None:
        # Should look something like
        #            col1  col2 filled_column
        # 0     2     4  Filled Value
        # 1     5    10  Filled Value
        print(pipeline_result.result)
    else:
        print("No results!")


def _load_dataset_some_unique_way() -> pd.DataFrame:
    # Totally loaded from some other place
    return pd.DataFrame([{"col1": 2, "col2": 4}, {"col1": 5, "col2": 10}])


if __name__ == "__main__":
    asyncio.run(run())
