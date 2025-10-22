# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""Copy root build assets to package directories."""

import shutil
from pathlib import Path


def copy_build_assets():
    """Copy root build assets to package build directories so files are included in pypi distributions."""
    root_dir = Path(__file__).parent.parent
    build_assets = ["LICENSE"]

    for package_dir in root_dir.glob("packages/*"):
        if package_dir.is_dir():
            for asset in build_assets:
                src = root_dir / asset
                dest = package_dir / asset
                if src.exists():
                    shutil.copy(src, dest)


if __name__ == "__main__":
    copy_build_assets()
