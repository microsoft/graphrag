# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A logger that emits updates from the indexing engine to the console."""

from graphrag.callbacks.noop_workflow_callbacks import NoopWorkflowCallbacks
from graphrag.index.typing.pipeline_run_result import PipelineRunResult
from graphrag.logger.progress import Progress

# ruff: noqa: T201


class ConsoleWorkflowCallbacks(NoopWorkflowCallbacks):
    """A logger that writes to a console."""

    _verbose = False

    def __init__(self, verbose=False):
        self._verbose = verbose

    def pipeline_start(self, names: list[str]) -> None:
        """Execute this callback to signal when the entire pipeline starts."""
        print("Starting pipeline with workflows:", ", ".join(names))

    def pipeline_end(self, results: list[PipelineRunResult]) -> None:
        """Execute this callback to signal when the entire pipeline ends."""
        print("Pipeline complete")

    def workflow_start(self, name: str, instance: object) -> None:
        """Execute this callback when a workflow starts."""
        print(f"Starting workflow: {name}")

    def workflow_end(self, name: str, instance: object) -> None:
        """Execute this callback when a workflow ends."""
        print("")  # account for potential return on prior progress
        print(f"Workflow complete: {name}")
        if self._verbose:
            print(instance)

    def progress(self, progress: Progress) -> None:
        """Handle when progress occurs."""
        complete = progress.completed_items or 0
        total = progress.total_items or 1
        percent = round((complete / total) * 100)
        start = f"  {complete} / {total} "
        print(f"{start:{'.'}<{percent}}", flush=True, end="\r")
