#!/usr/bin/env python3
"""
wrapper around the root 
"""

import sys
import os
from typing import List
if sys.platform.startswith("win"):
    from .windows import elevate as _elevate
else:
    from .posix import elevate as _elevate
    from .posix import Elevate


def elevate(show_console=True, graphical=False):
    """
    Re-launch the current process with root/admin privileges

    When run as root, this function does nothing.

    When not run as root, this function replaces the current process (Linux,
    macOS) or creates a child process, waits, and exits (Windows).

    :param show_console: (Windows only) if True, show a new console for the
        child process. Ignored on Linux / macOS.
    :param graphical: (Linux / macOS only) if True, attempt to use graphical
        programs (gksudo, etc). Ignored on Windows.
    """
    _elevate(show_console, graphical)


def run_as_root(cmds: List[str]):
    """
    :param cmds: a single command represented in a list of strings
    :return the return value of the command.
    """
    from subprocess import Popen, PIPE, STDOUT
    elevate()
    with Popen(cmds, stdout=PIPE, stderr=STDOUT, universal_newlines=True) as p:
        p.wait()
        assert p.returncode
        assert p.stdout
        return p.returncode, p.stdout.read()


def is_root():
    """
    :return true/false if root or not
    """
    return os.getuid() == 0


#if __name__ == '__main__':
#    # just a few tests
#    print("before ", is_root())
#    elevate()
#    print("after ", is_root())
