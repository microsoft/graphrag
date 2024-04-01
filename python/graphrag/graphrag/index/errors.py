#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""GraphRAG indexing error types."""


class NoWorkflowsDefinedError(ValueError):
    """Exception for no workflows defined."""

    def __init__(self):
        super().__init__("No workflows defined.")


class UndefinedWorkflowError(ValueError):
    """Exception for invalid verb input."""

    def __init__(self):
        super().__init__("Workflow name is undefined.")


class UnknownWorkflowError(ValueError):
    """Exception for invalid verb input."""

    def __init__(self, name: str):
        super().__init__(f"Unknown workflow: {name}")
