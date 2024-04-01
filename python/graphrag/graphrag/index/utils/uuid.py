#
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project.
#

"""UUID utilities."""
import uuid
from random import Random, getrandbits


def gen_uuid(rd: Random | None = None):
    """Generate a random UUID v4."""
    return uuid.UUID(
        int=rd.getrandbits(128) if rd is not None else getrandbits(128), version=4
    ).hex
