# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Helper utilities for LLM context injection in workflows."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def inject_llm_context(context: Any) -> None:
    """Inject pipeline context into ModelManager for LLM usage tracking.
    
    This helper function sets up LLM usage tracking for the current workflow.
    
    Args
    ----
        context: The PipelineRunContext containing stats and workflow information.
    
    Example
    -------
        from graphrag.index.utils.llm_context import inject_llm_context
        
        async def run_workflow(config, context):
            inject_llm_context(context)  # Enable LLM usage tracking
    
    Notes
    -----
        - This function is idempotent - calling it multiple times is safe
        - Failures are logged but don't break workflows
        - Only affects LLM models created via ModelManager
    """
    from graphrag.language_model.manager import ModelManager
    
    try:
        ModelManager().set_pipeline_context(context)
    except Exception as e:
        # Log warning but don't break workflow
        logger.warning("Failed to inject LLM context into ModelManager: %s", e)
