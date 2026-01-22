# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Jinja template engine."""

from typing import TYPE_CHECKING, Any

from jinja2 import StrictUndefined, Template, UndefinedError

from graphrag_llm.templating.template_engine import TemplateEngine

if TYPE_CHECKING:
    from graphrag_llm.templating.template_manager import TemplateManager


class JinjaTemplateEngine(TemplateEngine):
    """Jinja template engine."""

    _templates: dict[str, Template]
    _template_manager: "TemplateManager"

    def __init__(self, *, template_manager: "TemplateManager", **kwargs: Any) -> None:
        """Initialize the template engine.

        Args
        ----
            template_manager: TemplateManager
                The template manager to use for loading templates.
        """
        self._templates = {}
        self._template_manager = template_manager

    def render(self, template_name: str, context: dict[str, Any]) -> str:
        """Render a template with the given context."""
        jinja_template = self._templates.get(template_name)
        if jinja_template is None:
            template_contents = self._template_manager.get(template_name)
            if template_contents is None:
                msg = f"Template '{template_name}' not found."
                raise KeyError(msg)
            jinja_template = Template(template_contents, undefined=StrictUndefined)
            self._templates[template_name] = jinja_template
        try:
            return jinja_template.render(**context)
        except UndefinedError as e:
            msg = f"Missing key in context for template '{template_name}': {e.message}"
            raise KeyError(msg) from e
        except Exception as e:
            msg = f"Error rendering template '{template_name}': {e!s}"
            raise RuntimeError(msg) from e

    @property
    def template_manager(self) -> "TemplateManager":
        """Template manager associated with this engine."""
        return self._template_manager
