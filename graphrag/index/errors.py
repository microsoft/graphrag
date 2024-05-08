# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

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
