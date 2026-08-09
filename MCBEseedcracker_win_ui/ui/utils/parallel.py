# -*- coding: utf-8 -*-
"""
Process count helpers

Using every core causes DLL loading conflicts, memory bandwidth saturation and
cache contention, so the worker count is capped regardless of core count.
"""
import multiprocessing as mp

PROCESS_LIMIT = 16


def max_process_count():
    """Get the highest worker count allowed on this machine"""
    return min(mp.cpu_count(), PROCESS_LIMIT)


def resolve_process_count(user_process_count=None, log_prefix="INFO"):
    """Clamp a user-requested worker count to the allowed maximum"""
    allowed = max_process_count()

    if user_process_count is None:
        return allowed

    if user_process_count > allowed:
        print(f"[{log_prefix}] Limiting processes from {user_process_count} to {allowed} (to prevent resource exhaustion)")
    return min(user_process_count, allowed)
