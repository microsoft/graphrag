# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Abstract base class for template engines."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from graphrag_llm.templating.template_manager import TemplateManager


class TemplateEngine(ABC):
    """Abstract base class for template engines."""

    @abstractmethod
    def __init__(self, *, template_manager: "TemplateManager", **kwargs: Any) -> None:
        """Initialize the template engine.

        Args
        ----
            template_manager: TemplateManager
                The template manager to use for loading templates.

        """
        raise NotImplementedError

    @abstractmethod
    def render(self, template_name: str, context: dict[str, Any]) -> str:
        """Render a template with the given context.

        Args
        ----
            template_name: str
                The name of the template to render.
            context: dict[str, str]
                The context to use for rendering the template.

        Returns
        -------
            str: The rendered template.

        Raises
        ------
            KeyError: If the template is not found or a required key is missing in the context.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def template_manager(self) -> "TemplateManager":
        """Template manager associated with this engine."""
        raise NotImplementedError
