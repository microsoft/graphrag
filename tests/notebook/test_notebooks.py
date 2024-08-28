# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import subprocess
from pathlib import Path

import nbformat
import pytest

NOTEBOOKS_PATH = Path("examples_notebooks")
EXCLUDED_PATH = NOTEBOOKS_PATH / "community_contrib"

notebooks_list = [
    notebook
    for notebook in NOTEBOOKS_PATH.rglob("*.ipynb")
    if EXCLUDED_PATH not in notebook.parents
]


def _notebook_run(filepath: Path):
    """Execute a notebook via nbconvert and collect output.
    :returns execution errors
    """
    args = [
        "jupyter",
        "nbconvert",
        "--to",
        "notebook",
        "--execute",
        "-y",
        "--no-prompt",
        "--stdout",
        filepath.absolute().as_posix(),
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


@pytest.mark.parametrize("notebook_path", notebooks_list)
def test_notebook(notebook_path: Path):
    assert _notebook_run(notebook_path) == []
