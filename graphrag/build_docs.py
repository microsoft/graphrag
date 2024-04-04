# Copyright (c) 2024 Microsoft Corporation. All rights reserved.

"""A script utility to build verb-specific documentation for the Docsite."""

import ast
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


@dataclass
class Doc:
    """A data class for extracted Documentation."""

    file: str
    name: str
    documentation: str
    type: str

    @property
    def preamble(self) -> str:
        """The documentation preamble."""
        return f"""---
title: {self.name}
navtitle: {self.name}
layout: page
tags: [post, {self.type}]
---
"""

    @property
    def codelink(self) -> str:
        """The documentation code link."""
        basename = Path(self.file).name
        return f"""
## Code
[{basename}](https://github.com/microsoft/graphrag/blob/main/graphrag/{self.file})
"""

    @property
    def full_content(self) -> str:
        """The full content of the documentation."""
        return f"{self.preamble}{self.documentation}\n{self.codelink}".strip()


def _get_verb_documentation(content: str, file: str) -> list[Doc]:
    result: list[Doc] = []

    class VerbFunctionVisitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):  # noqa N802
            decorators = node.decorator_list
            if len(decorators) == 0:
                return

            for decorator in decorators:
                dec: Any = decorator
                name: ast.Name = dec.func
                if name is not None and name.id == "verb":
                    doc = ast.get_docstring(node)
                    if doc is not None:
                        result.append(
                            Doc(
                                name=node.name.replace("_verb", ""),
                                documentation=doc,
                                file=file,
                                type="verb",
                            )
                        )

    parsed = ast.parse(content)
    VerbFunctionVisitor().visit(parsed)
    return result


def _get_workflow_documentation(content: str, file: str) -> list[Doc]:
    result: list[Doc] = []

    class WorkflowFunctionVisitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):  # noqa N802
            doc = ast.get_docstring(node)
            if doc is not None:
                result.append(
                    Doc(
                        name=Path(file).name.replace(".py", ""),
                        documentation=doc,
                        file=file,
                        type="workflow",
                    )
                )

    parsed = ast.parse(content)
    WorkflowFunctionVisitor().visit(parsed)
    return result


verb_files = Path("graphrag/index/verbs").rglob("**/*.py")
docs_root = "docsite/posts/index"

for verb_file in verb_files:
    with Path(verb_file).open() as file:
        content = file.read()
        verb_docs = _get_verb_documentation(content, f"{verb_file}")
        verb_folder = Path(docs_root) / "verbs"
        verb_folder.mkdir(parents=True, exist_ok=True)
        for verb in verb_docs:
            with (verb_folder / f"{verb.name}.md").open("w") as file:
                file.write(verb.full_content)
                log.info("Wrote %s.md", verb.name)

workflow_files = Path("graphrag/index/workflows/v1").rglob("create_*.py")
for workflow_file in workflow_files:
    with Path(workflow_file).open() as file:
        content = file.read()
        workflow_docs = _get_workflow_documentation(content, f"{workflow_file}")
        workflow_folder = Path(docs_root) / "workflows"
        workflow_folder.mkdir(parents=True, exist_ok=True)
        for workflow in workflow_docs:
            with (workflow_folder / f"{workflow.name}.md").open("w") as file:
                file.write(workflow.full_content)
                log.info("Wrote %s.md", workflow.name)
