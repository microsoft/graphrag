# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import subprocess
from dataclasses import dataclass
from pathlib import Path

import nbformat
import pytest


@dataclass
class NotebookDetails:
    dir: Path
    excluded_filenames: list[str]


NOTEBOOKS: list[NotebookDetails] = [
    NotebookDetails(
        dir=Path("packages/graphrag-llm/notebooks"),
        excluded_filenames=[],
    ),
    # Was in previous test but not actually pointing at a notebooks location
    # NotebookDetails(
    #     dir=Path("examples_notebooks"),  # noqa: ERA001
    #     excluded_filenames=["community_contrib"],  # noqa: ERA001
    # ),
]

notebooks_list = [
    nb
    for details in NOTEBOOKS
    for nb in details.dir.rglob("*.ipynb")
    if nb.stem not in details.excluded_filenames
]


def _notebook_run(filepath: Path):
    """Execute a notebook via nbconvert and collect output.
    :returns execution errors
    """
    args = [
        "uv",
        "run",
        "jupyter",
        "nbconvert",
        "--to",
        "notebook",
        "--execute",
        "-y",
        "--no-prompt",
        "--stdout",
        str(filepath.resolve()),
    ]
    notebook = subprocess.check_output(args)
    nb = nbformat.reads(notebook, nbformat.current_nbformat)

    return [
        output
        for cell in nb.cells
        if "outputs" in cell
        for output in cell["outputs"]
        if output.output_type == "error"
    ]


def clear_cache():
    cache_dir = Path("packages/graphrag-llm/notebooks/cache")
    if cache_dir.exists():
        for file in cache_dir.iterdir():
            if file.is_file():
                file.unlink()
        cache_dir.rmdir()


clear_cache()


@pytest.mark.parametrize("notebook_path", notebooks_list)
def test_notebook(notebook_path: Path):
    assert _notebook_run(notebook_path) == []
