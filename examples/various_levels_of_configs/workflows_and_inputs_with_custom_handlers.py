# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import asyncio
import os
from typing import Any

from datashaper import NoopWorkflowCallbacks, Progress

from graphrag.index import run_pipeline_with_config
from graphrag.index.cache import InMemoryCache, PipelineCache
from graphrag.index.storage import MemoryPipelineStorage


async def main():
    if (
        "EXAMPLE_OPENAI_API_KEY" not in os.environ
        and "OPENAI_API_KEY" not in os.environ
    ):
        msg = "Please set EXAMPLE_OPENAI_API_KEY or OPENAI_API_KEY environment variable to run this example"
        raise Exception(msg)

    # run the pipeline with the config, and override the dataset with the one we just created
    # and grab the last result from the pipeline, should be our entity extraction
    pipeline_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "./pipelines/workflows_and_inputs.yml",
    )

    # Create our custom storage
    custom_storage = ExampleStorage()

    # Create our custom reporter
    custom_reporter = ExampleReporter()

    # Create our custom cache
    custom_cache = ExampleCache()

    # run the pipeline with the config, and override the dataset with the one we just created
    # and grab the last result from the pipeline, should be the last workflow that was run (our nodes)
    pipeline_result = []
    async for result in run_pipeline_with_config(
        pipeline_path,
        storage=custom_storage,
        callbacks=custom_reporter,
        cache=custom_cache,
    ):
        pipeline_result.append(result)
    pipeline_result = pipeline_result[-1]

    # The output will contain a list of positioned nodes
    if pipeline_result.result is not None:
        top_nodes = pipeline_result.result.head(10)
        print("pipeline result", top_nodes)
    else:
        print("No results!")


class ExampleStorage(MemoryPipelineStorage):
    """Example of a custom storage handler"""

    async def get(
        self, key: str, as_bytes: bool | None = None, encoding: str | None = None
    ) -> Any:
        print(f"ExampleStorage.get {key}")
        return await super().get(key, as_bytes)

    async def set(
        self, key: str, value: str | bytes | None, encoding: str | None = None
    ) -> None:
        print(f"ExampleStorage.set {key}")
        return await super().set(key, value)

    async def has(self, key: str) -> bool:
        print(f"ExampleStorage.has {key}")
        return await super().has(key)

    async def delete(self, key: str) -> None:
        print(f"ExampleStorage.delete {key}")
        return await super().delete(key)

    async def clear(self) -> None:
        print("ExampleStorage.clear")
        return await super().clear()


class ExampleCache(InMemoryCache):
    """Example of a custom cache handler"""

    async def get(self, key: str) -> Any:
        print(f"ExampleCache.get {key}")
        return await super().get(key)

    async def set(self, key: str, value: Any, debug_data: dict | None = None) -> None:
        print(f"ExampleCache.set {key}")
        return await super().set(key, value, debug_data)

    async def has(self, key: str) -> bool:
        print(f"ExampleCache.has {key}")
        return await super().has(key)

    async def delete(self, key: str) -> None:
        print(f"ExampleCache.delete {key}")
        return await super().delete(key)

    async def clear(self) -> None:
        print("ExampleCache.clear")
        return await super().clear()

    def child(self, name: str) -> PipelineCache:
        print(f"ExampleCache.child {name}")
        return ExampleCache(name)


class ExampleReporter(NoopWorkflowCallbacks):
    """Example of a custom reporter.  This will print out all of the status updates from the pipeline."""

    def progress(self, progress: Progress):
        print("ExampleReporter.progress: ", progress)

    def error(self, message: str, details: dict[str, Any] | None = None):
        print("ExampleReporter.error: ", message)

    def warning(self, message: str, details: dict[str, Any] | None = None):
        print("ExampleReporter.warning: ", message)

    def log(self, message: str, details: dict[str, Any] | None = None):
        print("ExampleReporter.log: ", message)


if __name__ == "__main__":
    asyncio.run(main())
