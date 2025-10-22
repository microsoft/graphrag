# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Template manager factory implementation."""

from collections.abc import Callable
from typing import TYPE_CHECKING

from graphrag_common.factory import Factory

from graphrag_llm.config.template_engine_config import TemplateEngineConfig
from graphrag_llm.config.types import TemplateManagerType
from graphrag_llm.templating.template_manager import TemplateManager

if TYPE_CHECKING:
    from graphrag_common.factory import ServiceScope


class TemplateManagerFactory(Factory[TemplateManager]):
    """Factory for creating template manager instances."""


template_manager_factory = TemplateManagerFactory()


def register_template_manager(
    template_manager_type: str,
    template_manager_initializer: Callable[..., TemplateManager],
    scope: "ServiceScope" = "transient",
) -> None:
    """Register a custom template manager implementation.

    Args
    ----
        - template_manager_type: str
            The template manager id to register.
        - template_manager_initializer: Callable[..., TemplateManager]
            The template manager initializer to register.
    """
    template_manager_factory.register(
        strategy=template_manager_type,
        initializer=template_manager_initializer,
        scope=scope,
    )


def create_template_manager(
    template_engine_config: TemplateEngineConfig | None = None,
) -> TemplateManager:
    """Create a TemplateManager instance.

    Args
    ----
        template_engine_config: TemplateEngineConfig
            The configuration for the template engine.

    Returns
    -------
        TemplateManager:
            An instance of a TemplateManager subclass.
    """
    template_engine_config = template_engine_config or TemplateEngineConfig()
    strategy = template_engine_config.template_manager
    init_args = template_engine_config.model_dump()

    if strategy not in template_manager_factory:
        match strategy:
            case TemplateManagerType.File:
                from graphrag_llm.templating.file_template_manager import (
                    FileTemplateManager,
                )

                template_manager_factory.register(
                    strategy=TemplateManagerType.File,
                    initializer=FileTemplateManager,
                    scope="singleton",
                )
            case _:
                msg = f"TemplateEngineConfig.template_manager '{strategy}' is not registered in the TemplateManagerFactory. Registered strategies: {', '.join(template_manager_factory.keys())}"
                raise ValueError(msg)

    return template_manager_factory.create(strategy=strategy, init_args=init_args)
