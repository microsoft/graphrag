# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""CLI implementation of the initialization subcommand."""

from pathlib import Path

from graphrag.config.init_content import INIT_DOTENV, INIT_YAML
from graphrag.logger.factory import LoggerFactory, LoggerType
from graphrag.prompts.index.claim_extraction import CLAIM_EXTRACTION_PROMPT
from graphrag.prompts.index.community_report import (
    COMMUNITY_REPORT_PROMPT,
)
from graphrag.prompts.index.entity_extraction import GRAPH_EXTRACTION_PROMPT
from graphrag.prompts.index.summarize_descriptions import SUMMARIZE_PROMPT
from graphrag.prompts.query.drift_search_system_prompt import DRIFT_LOCAL_SYSTEM_PROMPT
from graphrag.prompts.query.global_search_knowledge_system_prompt import (
    GENERAL_KNOWLEDGE_INSTRUCTION,
)
from graphrag.prompts.query.global_search_map_system_prompt import MAP_SYSTEM_PROMPT
from graphrag.prompts.query.global_search_reduce_system_prompt import (
    REDUCE_SYSTEM_PROMPT,
)
from graphrag.prompts.query.local_search_system_prompt import LOCAL_SEARCH_SYSTEM_PROMPT
from graphrag.prompts.query.question_gen_system_prompt import QUESTION_SYSTEM_PROMPT


def initialize_project_at(path: Path) -> None:
    """Initialize the project at the given path."""
    progress_logger = LoggerFactory().create_logger(LoggerType.RICH)
    progress_logger.info(f"Initializing project at {path}")  # noqa: G004
    root = Path(path)
    if not root.exists():
        root.mkdir(parents=True, exist_ok=True)

    settings_yaml = root / "settings.yaml"
    if settings_yaml.exists():
        msg = f"Project already initialized at {root}"
        raise ValueError(msg)

    with settings_yaml.open("wb") as file:
        file.write(INIT_YAML.encode(encoding="utf-8", errors="strict"))

    dotenv = root / ".env"
    if not dotenv.exists():
        with dotenv.open("wb") as file:
            file.write(INIT_DOTENV.encode(encoding="utf-8", errors="strict"))

    prompts_dir = root / "prompts"
    if not prompts_dir.exists():
        prompts_dir.mkdir(parents=True, exist_ok=True)

    prompts = {
        "entity_extraction": GRAPH_EXTRACTION_PROMPT,
        "summarize_descriptions": SUMMARIZE_PROMPT,
        "claim_extraction": CLAIM_EXTRACTION_PROMPT,
        "community_report": COMMUNITY_REPORT_PROMPT,
        "drift_search_system_prompt": DRIFT_LOCAL_SYSTEM_PROMPT,
        "global_search_map_system_prompt": MAP_SYSTEM_PROMPT,
        "global_search_reduce_system_prompt": REDUCE_SYSTEM_PROMPT,
        "global_search_knowledge_system_prompt": GENERAL_KNOWLEDGE_INSTRUCTION,
        "local_search_system_prompt": LOCAL_SEARCH_SYSTEM_PROMPT,
        "question_gen_system_prompt": QUESTION_SYSTEM_PROMPT,
    }

    for name, content in prompts.items():
        prompt_file = prompts_dir / f"{name}.txt"
        if not prompt_file.exists():
            with prompt_file.open("wb") as file:
                file.write(content.encode(encoding="utf-8", errors="strict"))
