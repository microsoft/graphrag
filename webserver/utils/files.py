import os
from datetime import datetime


def get_sorted_subdirs(directory: str):
    """Get sorted subdirectory names in the specified directory."""
    subdirs = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d)) and not d.startswith('.')]
    subdirs_sorted = sorted(subdirs, key=lambda x: datetime.strptime(x, "%Y%m%d-%H%M%S"), reverse=True)
    return subdirs_sorted


def get_latest_subdir(directory: str):
    # current, we only support date like output folder.
    subdirs = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d)) and not d.startswith('.')]
    if not subdirs:
        raise ValueError(f"No subdirectories found in {directory}")
    subdirs_sorted = sorted(subdirs, key=lambda x: datetime.strptime(x, "%Y%m%d-%H%M%S"), reverse=True)
    return subdirs_sorted[0]
