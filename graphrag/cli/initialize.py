# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""CLI implementation of the initialization subcommand."""

from pathlib import Path

from graphrag.config.init_content import INIT_DOTENV, INIT_YAML
from graphrag.logger.factory import LoggerFactory, LoggerType
from graphrag.prompts.index.community_report import (
    COMMUNITY_REPORT_PROMPT,
)
from graphrag.prompts.index.community_report_text_units import (
    COMMUNITY_REPORT_TEXT_PROMPT,
)
from graphrag.prompts.index.extract_claims import EXTRACT_CLAIMS_PROMPT
from graphrag.prompts.index.extract_graph import GRAPH_EXTRACTION_PROMPT
from graphrag.prompts.index.summarize_descriptions import SUMMARIZE_PROMPT
from graphrag.prompts.query.basic_search_system_prompt import BASIC_SEARCH_SYSTEM_PROMPT
from graphrag.prompts.query.drift_search_system_prompt import (
    DRIFT_LOCAL_SYSTEM_PROMPT,
    DRIFT_REDUCE_PROMPT,
)
from graphrag.prompts.query.global_search_knowledge_system_prompt import (
    GENERAL_KNOWLEDGE_INSTRUCTION,
)
from graphrag.prompts.query.global_search_map_system_prompt import MAP_SYSTEM_PROMPT
from graphrag.prompts.query.global_search_reduce_system_prompt import (
    REDUCE_SYSTEM_PROMPT,
)
from graphrag.prompts.query.local_search_system_prompt import LOCAL_SEARCH_SYSTEM_PROMPT
from graphrag.prompts.query.question_gen_system_prompt import QUESTION_SYSTEM_PROMPT


def initialize_project_at(path: Path, force: bool) -> None:
    """
    Initialize the project at the given path.

    Parameters
    ----------
    path : Path
        The path at which to initialize the project.
    force : bool
        Whether to force initialization even if the project already exists.

    Raises
    ------
    ValueError
        If the project already exists and force is False.
    """
    progress_logger = LoggerFactory().create_logger(LoggerType.RICH)
    progress_logger.info(f"Initializing project at {path}")  # noqa: G004
    root = Path(path)
    if not root.exists():
        root.mkdir(parents=True, exist_ok=True)

    settings_yaml = root / "settings.yaml"
    if settings_yaml.exists() and not force:
        msg = f"Project already initialized at {root}"
        raise ValueError(msg)

    with settings_yaml.open("wb") as file:
        file.write(INIT_YAML.encode(encoding="utf-8", errors="strict"))

    dotenv = root / ".env"
    if not dotenv.exists() or force:
        with dotenv.open("wb") as file:
            file.write(INIT_DOTENV.encode(encoding="utf-8", errors="strict"))

    prompts_dir = root / "prompts"
    if not prompts_dir.exists():
        prompts_dir.mkdir(parents=True, exist_ok=True)

    prompts = {
        "extract_graph": GRAPH_EXTRACTION_PROMPT,
        "summarize_descriptions": SUMMARIZE_PROMPT,
        "extract_claims": EXTRACT_CLAIMS_PROMPT,
        "community_report_graph": COMMUNITY_REPORT_PROMPT,
        "community_report_text": COMMUNITY_REPORT_TEXT_PROMPT,
        "drift_search_system_prompt": DRIFT_LOCAL_SYSTEM_PROMPT,
        "drift_reduce_prompt": DRIFT_REDUCE_PROMPT,
        "global_search_map_system_prompt": MAP_SYSTEM_PROMPT,
        "global_search_reduce_system_prompt": REDUCE_SYSTEM_PROMPT,
        "global_search_knowledge_system_prompt": GENERAL_KNOWLEDGE_INSTRUCTION,
        "local_search_system_prompt": LOCAL_SEARCH_SYSTEM_PROMPT,
        "basic_search_system_prompt": BASIC_SEARCH_SYSTEM_PROMPT,
        "question_gen_system_prompt": QUESTION_SYSTEM_PROMPT,
    }

    for name, content in prompts.items():
        prompt_file = prompts_dir / f"{name}.txt"
        if not prompt_file.exists() or force:
            with prompt_file.open("wb") as file:
                file.write(content.encode(encoding="utf-8", errors="strict"))
