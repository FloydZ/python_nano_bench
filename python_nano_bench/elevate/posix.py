#!/usr/bin/env python3

"""
linux/darwin/posix wrapper around sudo/gksudo,... or any privileges escalation
tool.
"""

import errno
import os
import sys
import threading
from multiprocessing.connection import Client
from typing import List, Tuple
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


def worker_send_command_blocking(cmd_queue, response_dict, commands):
    print( os.getuid())
    tid = threading.get_native_id()
    done_event = threading.Event()
    print(f"[Worker {tid}] Sending command to root executor...")
    cmd_queue.put((tid, commands, done_event))
    done_event.wait()
    stdout, stderr = response_dict.pop(tid)
    print(f"[Worker {tid}] Output:\n{stdout}")
    if stderr:
        print(f"[Worker {tid}] Error:\n{stderr}")



ADDRESS = ('localhost', 6000)
AUTHKEY = b'secret'

def main():
    conn = Client(ADDRESS, authkey=AUTHKEY)
    print("[Client] Connected to server.")

    messages = ["hello", "status", "exit"]
    for msg in messages:
        print(f"[Client] Sending: {msg}")
        conn.send(msg)
        reply = conn.recv()
        print(f"[Client] Server replied: {reply}")

    conn.close()

if __name__ == '__main__':
    main()
#if __name__ == "__main__":
#    print( os.getuid())
#    cmd_queue = queue.Queue()
#    response_dict = {}
#    root_executor = RootCommandExecutor(cmd_queue, response_dict)
#    root_executor.start()
#
#    # Simulate worker threads sending blocking commands
#    threading.Thread(target=worker_send_command_blocking, args=(cmd_queue, response_dict, ["ls", "/"])).start()
#    threading.Thread(target=worker_send_command_blocking, args=(cmd_queue, response_dict, ["whoami"])).start()
#
#    try:
#        while True:
#            time.sleep(1)
#    except KeyboardInterrupt:
#        print("\n[Main] Stopping root executor...")
#        root_executor.stop()
#        root_executor.join()
#        print("[Main] Shutdown complete.")
