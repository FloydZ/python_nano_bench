#!/usr/bin/env python3
"""
linux/darwin/posix wrapper around sudo/gksudo,... or any privileges escalation
tool.
"""

import errno
import os
import sys
from typing import List, Tuple
from subprocess import Popen, PIPE, STDOUT
from shlex import quote


def quote_shell(args):
    """
    :param args:
    :return
    """
    return " ".join(quote(arg) for arg in args)


def quote_applescript(string):
    """
    :param args:
    :return
    """
    charmap = {
        "\n": "\\n",
        "\r": "\\r",
        "\t": "\\t",
        "\"": "\\\"",
        "\\": "\\\\",
    }
    return '"%s"' % "".join(charmap.get(char, char) for char in string)


def elevate(_=True, graphical=True):
    """
    :param graphical:
    :return
    """
    if os.getuid() == 0:
        return

    args = [sys.executable] + sys.argv
    commands = []

    if graphical:
        if sys.platform.startswith("darwin"):
            commands.append([
                "osascript",
                "-e",
                "do shell script %s "
                "with administrator privileges "
                "without altering line endings"
                % quote_applescript(quote_shell(args))])

        if sys.platform.startswith("linux") and os.environ.get("DISPLAY"):
            commands.append(["pkexec"] + args)
            commands.append(["gksudo"] + args)
            commands.append(["kdesudo"] + args)

    commands.append(["sudo"] + args)

    for args in commands:
        try:
            os.execlp(args[0], *args)
        except OSError as e:
            if e.errno != errno.ENOENT or args[0] == "sudo":
                raise


class Elevate:
    """
    this class spawns a additional shell with root rights, and then forwards
    commands to this shell
    """
    def __init__(self) -> None:
        pass

    def run(self, cmds: List[str]) -> Tuple[int, str]:
        """
        TODO: einen process auslagern der die commands dann ausführt.

        :params cmds: list of str which form the command to execute
        :return returncode, stdout
        """
        elevate()

        with Popen(cmds, stdout=PIPE, stderr=STDOUT, universal_newlines=True) as p:
            p.wait()
            assert p.returncode
            assert p.stdout
            return p.returncode, p.stdout.read()

