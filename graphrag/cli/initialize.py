# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""CLI implementation of initialization subcommand."""

from pathlib import Path

from graphrag.index.graph.extractors.claims.prompts import CLAIM_EXTRACTION_PROMPT
from graphrag.index.graph.extractors.community_reports.prompts import (
    COMMUNITY_REPORT_PROMPT,
)
from graphrag.index.graph.extractors.graph.prompts import GRAPH_EXTRACTION_PROMPT
from graphrag.index.graph.extractors.summarize.prompts import SUMMARIZE_PROMPT
from graphrag.index.init_content import INIT_DOTENV, INIT_YAML
from graphrag.logging import ReporterType, create_progress_reporter


def initialize_project_at(path: Path) -> None:
    """Initialize the project at the given path."""
    progress_reporter = create_progress_reporter(ReporterType.RICH)
    progress_reporter.info(f"Initializing project at {path}")
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

    entity_extraction = prompts_dir / "entity_extraction.txt"
    if not entity_extraction.exists():
        with entity_extraction.open("wb") as file:
            file.write(
                GRAPH_EXTRACTION_PROMPT.encode(encoding="utf-8", errors="strict")
            )

    summarize_descriptions = prompts_dir / "summarize_descriptions.txt"
    if not summarize_descriptions.exists():
        with summarize_descriptions.open("wb") as file:
            file.write(SUMMARIZE_PROMPT.encode(encoding="utf-8", errors="strict"))

    claim_extraction = prompts_dir / "claim_extraction.txt"
    if not claim_extraction.exists():
        with claim_extraction.open("wb") as file:
            file.write(
                CLAIM_EXTRACTION_PROMPT.encode(encoding="utf-8", errors="strict")
            )

    community_report = prompts_dir / "community_report.txt"
    if not community_report.exists():
        with community_report.open("wb") as file:
            file.write(
                COMMUNITY_REPORT_PROMPT.encode(encoding="utf-8", errors="strict")
            )
