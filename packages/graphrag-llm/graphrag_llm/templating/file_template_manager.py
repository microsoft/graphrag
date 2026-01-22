# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""In-memory template manager implementation."""

from pathlib import Path
from typing import Any

from graphrag_llm.templating.template_manager import TemplateManager


class FileTemplateManager(TemplateManager):
    """Abstract base class for template managers."""

    _encoding: str
    _templates_extension: str
    _templates_dir: Path

    def __init__(
        self,
        base_dir: str = "templates",
        template_extension: str = ".jinja",
        encoding: str = "utf-8",
        **kwargs: Any,
    ) -> None:
        """Initialize the template manager.

        Args
        ----
            base_dir: str (default="./templates")
                The base directory where templates are stored.
            template_extension: str (default=".jinja")
                The file extension for template files.
            encoding: str (default="utf-8")
                The encoding used to read template files.

        Raises
        ------
            ValueError
                If the base directory does not exist or is not a directory.
                If the template_extension is an empty string.
        """
        self._templates = {}
        self._encoding = encoding

        self._templates_extension = template_extension

        self._templates_dir = Path(base_dir).resolve()
        if not self._templates_dir.exists() or not self._templates_dir.is_dir():
            msg = f"Templates directory '{base_dir}' does not exist or is not a directory."
            raise ValueError(msg)

    def get(self, template_name: str) -> str | None:
        """Retrieve a template by its name."""
        template_file = (
            self._templates_dir / f"{template_name}{self._templates_extension}"
        )
        if template_file.exists() and template_file.is_file():
            return template_file.read_text(encoding=self._encoding)
        return None

    def register(self, template_name: str, template: str) -> None:
        """Register a new template."""
        self._templates[template_name] = template
        template_path = (
            self._templates_dir / f"{template_name}{self._templates_extension}"
        )
        template_path.write_text(template, encoding=self._encoding)

    def keys(self) -> list[str]:
        """List all registered template names."""
        return list(self._templates.keys())

    def __contains__(self, template_name: str) -> bool:
        """Check if a template is registered."""
        return template_name in self._templates
