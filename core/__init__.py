# -*- coding: utf-8 -*-
"""MCBE seed cracker core: pure cracking logic shared by CLI, GUI and future frontends.

Import-safe under multiprocessing spawn: importing this package never loads a
native library, reads a config file or spawns a process pool.
"""
