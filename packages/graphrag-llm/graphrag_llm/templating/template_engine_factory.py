# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Template engine factory implementation."""

from collections.abc import Callable
from typing import TYPE_CHECKING

from graphrag_common.factory import Factory

from graphrag_llm.config.template_engine_config import TemplateEngineConfig
from graphrag_llm.config.types import TemplateEngineType
from graphrag_llm.templating.template_engine import TemplateEngine
from graphrag_llm.templating.template_manager_factory import create_template_manager

if TYPE_CHECKING:
    from graphrag_common.factory import ServiceScope


class TemplateEngineFactory(Factory[TemplateEngine]):
    """Factory for creating template engine instances."""


template_engine_factory = TemplateEngineFactory()


def register_template_engine(
    template_engine_type: str,
    template_engine_initializer: Callable[..., TemplateEngine],
    scope: "ServiceScope" = "transient",
) -> None:
    """Register a custom template engine implementation.

    Args
    ----
        template_engine_type: str
            The template engine id to register.
        template_engine_initializer: Callable[..., TemplateEngine]
            The template engine initializer to register.
        scope: ServiceScope (default: "transient")
            The service scope for the template engine instance.
    """
    template_engine_factory.register(
        strategy=template_engine_type,
        initializer=template_engine_initializer,
        scope=scope,
    )


def create_template_engine(
    template_engine_config: TemplateEngineConfig | None = None,
) -> TemplateEngine:
    """Create a TemplateEngine instance.

    Args
    ----
        template_engine_config: TemplateEngineConfig | None
            The configuration for the template engine. If None, defaults will be used.

    Returns
    -------
        TemplateEngine:
            An instance of a TemplateEngine subclass.
    """
    template_engine_config = template_engine_config or TemplateEngineConfig()

    strategy = template_engine_config.type
    template_manager = create_template_manager(
        template_engine_config=template_engine_config
    )
    init_args = template_engine_config.model_dump()

    if strategy not in template_engine_factory:
        match strategy:
            case TemplateEngineType.Jinja:
                from graphrag_llm.templating.jinja_template_engine import (
                    JinjaTemplateEngine,
                )

                template_engine_factory.register(
                    strategy=TemplateEngineType.Jinja,
                    initializer=JinjaTemplateEngine,
                    scope="singleton",
                )
            case _:
                msg = f"TemplateEngineConfig.type '{strategy}' is not registered in the TemplateEngineFactory. Registered strategies: {', '.join(template_engine_factory.keys())}"
                raise ValueError(msg)

    return template_engine_factory.create(
        strategy=strategy,
        init_args={
            **init_args,
            "template_manager": template_manager,
        },
    )
