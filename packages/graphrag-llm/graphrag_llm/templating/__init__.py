# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Templates module."""

from graphrag_llm.templating.template_engine import TemplateEngine
from graphrag_llm.templating.template_engine_factory import (
    create_template_engine,
    register_template_engine,
)
from graphrag_llm.templating.template_manager import TemplateManager
from graphrag_llm.templating.template_manager_factory import (
    create_template_manager,
    register_template_manager,
)

__all__ = [
    "TemplateEngine",
    "TemplateManager",
    "create_template_engine",
    "create_template_manager",
    "register_template_engine",
    "register_template_manager",
]
