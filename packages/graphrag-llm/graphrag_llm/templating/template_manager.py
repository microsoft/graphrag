# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Abstract base class for template managers."""

from abc import ABC, abstractmethod
from typing import Any


class TemplateManager(ABC):
    """Abstract base class for template managers."""

    @abstractmethod
    def __init__(self, **kwargs: Any) -> None:
        """Initialize the template manager."""
        raise NotImplementedError

    @abstractmethod
    def get(self, template_name: str) -> str | None:
        """Retrieve a template by its name.

        Args
        ----
            template_name: str
                The name of the template to retrieve.

        Returns
        -------
            str | None: The content of the template, if found.
        """
        raise NotImplementedError

    @abstractmethod
    def register(self, template_name: str, template: str) -> None:
        """Register a new template.

        Args
        ----
            template_name: str
                The name of the template.
            template: str
                The content of the template.
        """
        raise NotImplementedError

    @abstractmethod
    def keys(self) -> list[str]:
        """List all registered template names.

        Returns
        -------
            list[str]: A list of registered template names.
        """
        raise NotImplementedError

    @abstractmethod
    def __contains__(self, template_name: str) -> bool:
        """Check if a template is registered.

        Args
        ----
            template_name: str
                The name of the template to check.
        """
        raise NotImplementedError
