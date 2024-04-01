#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""The Indexing Engine overrides package root."""
from .aggregate import aggregate
from .concat import concat
from .merge import merge

__all__ = ["aggregate", "concat", "merge"]
