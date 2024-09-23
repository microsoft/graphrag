# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Bootstrap definition."""

import warnings

# Ignore warnings from numba
warnings.filterwarnings("ignore", message=".*The 'nopython' keyword.*")
warnings.filterwarnings("ignore", message=".*Use no seed for parallelism.*")

initialized_nltk = False


def bootstrap():
    """Bootstrap definition."""
    global initialized_nltk
    if not initialized_nltk:
        import nltk
        from nltk.corpus import wordnet as wn

        nltk.download("punkt")
        nltk.download("averaged_perceptron_tagger")
        nltk.download("maxent_ne_chunker")
        nltk.download("words")
        nltk.download("wordnet")
        wn.ensure_loaded()
        initialized_nltk = True
