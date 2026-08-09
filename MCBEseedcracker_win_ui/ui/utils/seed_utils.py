# -*- coding: utf-8 -*-
"""
Seed helpers - conversion between the unsigned DLL output and the in-game seed
"""

MAX_UINT32 = 4294967295
# Upper bound of the reduced range used by test mode
TEST_MODE_END = 100000000
SIGNED64_MAX = 9223372036854775807
UINT64_MAX = 18446744073709551615


def to_signed64(seed):
    """Convert an unsigned 64-bit seed to the signed value shown in game"""
    if seed > SIGNED64_MAX:
        return seed - UINT64_MAX - 1
    return seed
