#!/usr/bin/env python3

"""
linux/darwin/posix wrapper around sudo/gksudo,... or any privileges escalation
tool.
"""

import errno
import json
import os
import sys
from multiprocessing.connection import Client
from typing import List
from shlex import quote

from python_nano_bench.elevate.secrets import ADDRESS, AUTHKEY


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


def elevate(_=True, graphical=False):
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

#TODO remove
class Elevate():
    pass

def worker_send_command_blocking(cmd: List[str]):
    conn = Client(ADDRESS, authkey=AUTHKEY)
    print("[Client] Connected to server.")
    msg = json.dumps(cmd)
    print(f"[Client] send: {msg}.")
    conn.send(msg)
    reply = conn.recv()
    print(f"[Client] recv: {reply}.")
    conn.close()
    print(f"[Client] closed")
    return reply


if __name__ == '__main__':
    pass
