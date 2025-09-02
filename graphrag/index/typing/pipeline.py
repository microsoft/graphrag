# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the Pipeline class."""

from collections.abc import Generator

from graphrag.index.typing.workflow import Workflow


class Pipeline:
    """Encapsulates running workflows."""

    def __init__(self, workflows: list[Workflow]):
        self.workflows = workflows

    def run(self) -> Generator[Workflow]:
        """Return a Generator over the pipeline workflows."""
        yield from self.workflows

    def names(self) -> list[str]:
        """Return the names of the workflows in the pipeline."""
        return [name for name, _ in self.workflows]

    def remove(self, name: str) -> None:
        """Remove a workflow from the pipeline by name."""
        self.workflows = [w for w in self.workflows if w[0] != name]
