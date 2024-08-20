# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
import subprocess
import tempfile
import os
from pathlib import Path

import nbformat
import pytest

NOTEBOOKS_PATH = Path("examples_notebooks")

notebooks_list = list(NOTEBOOKS_PATH.rglob("*.ipynb"))


def _notebook_run(filepath: Path):
    """Execute a notebook via nbconvert and collect output.
    :returns execution errors
    """
    print(os.environ.get("TMP"))
    print(os.environ.get("TEMP"))
    with tempfile.NamedTemporaryFile(suffix=".ipynb", dir=os.environ.get("TMP")) as temp_file:
        args = [
            "jupyter",
            "nbconvert",
            "--to",
            "notebook",
            "--execute",
            "-y",
            "--no-prompt",
            "--output",
            temp_file.name,
            filepath.absolute().as_posix(),
        ]
        subprocess.check_call(args)

        temp_file.seek(0)
        nb = nbformat.read(temp_file, nbformat.current_nbformat)

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
