# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""A module containing the base LLM class."""

def BaseLLM(Protocol):
    """A base class for LLMs."""
    def __init__(self):
        pass

    def get_response(self, input: str) -> str:
        """Get a response from the LLM."""
        pass

    def get_embedding(self, input: str) -> list[float]:
        """Get an embedding from the LLM."""
        pass