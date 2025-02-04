# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Util functions needed for nltk-based noun-phrase extractors (i.e. TextBlob)."""

import nltk


def download_if_not_exists(resource_name) -> bool:
    """Download nltk resources if they haven't been already."""
    # look under all possible categories
    root_categories = [
        "corpora",
        "tokenizers",
        "taggers",
        "chunkers",
        "classifiers",
        "stemmers",
        "stopwords",
        "languages",
        "frequent",
        "gate",
        "models",
        "mt",
        "sentiment",
        "similarity",
    ]
    for category in root_categories:
        try:
            # if found, stop looking and avoid downloading
            nltk.find(f"{category}/{resource_name}")
            return True  # noqa: TRY300
        except LookupError:
            continue

    # is not found, download
    nltk.download(resource_name)
    return False
