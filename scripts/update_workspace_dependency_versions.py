# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Update workspace dependency versions."""

import os
import re
import subprocess  # noqa: S404
from pathlib import Path


def _get_version() -> str:
    command = ["uv", "run", "semversioner", "current-version"]
    completion = subprocess.run(command, env=os.environ, capture_output=True, text=True)  # noqa: S603
    if completion.returncode != 0:
        msg = f"Failed to get current version with return code: {completion.returncode}"
        raise RuntimeError(msg)
    return completion.stdout.strip()


def _get_package_paths() -> list[Path]:
    root_dir = Path(__file__).parent.parent
    return [p.resolve() for p in root_dir.glob("packages/*") if p.is_dir()]


def update_workspace_dependency_versions():
    """Update dependency versions across workspace packages.

    Iterate through all the workspace packages and update cross-package
    dependency versions to match the current version of the workspace.
    """
    version = _get_version()
    package_paths = _get_package_paths()
    for package_path in package_paths:
        current_package_name = package_path.name
        toml_path = package_path / "pyproject.toml"
        if not toml_path.exists() or not toml_path.is_file():
            continue
        toml_contents = toml_path.read_text(encoding="utf-8")

        for other_package_path in package_paths:
            other_package_name = other_package_path.name
            if other_package_name == current_package_name:
                continue
            dep_pattern = rf"{other_package_name}\s*==\s*\d+\.\d+\.\d+"

            if re.search(dep_pattern, toml_contents):
                toml_contents = re.sub(
                    dep_pattern,
                    f"{other_package_name}=={version}",
                    toml_contents,
                )

        toml_path.write_text(toml_contents, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    update_workspace_dependency_versions()
