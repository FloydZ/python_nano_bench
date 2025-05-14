#!/usr/bin/env python3
import json
from multiprocessing.connection import Listener
import threading
from subprocess import Popen, PIPE, STDOUT

from .posix import elevate
from .secrets import ADDRESS, AUTHKEY


class RootCommandExecutor(threading.Thread):
    """
    this class spawns an additional shell with root rights, and then forwards
    commands to this shell
    """
    def __init__(self) -> None:
        super().__init__(daemon=True, name="RootCommandExecutor")
        self._stop_event = threading.Event()

    def run(self):
        """
        TODO
        """
        tid = threading.get_native_id()
        print(f"[Server: {tid}] start ")

        listener = Listener(ADDRESS, authkey=AUTHKEY)
        print(f"[Server] Listening on {ADDRESS}...")

        conn = listener.accept()
        print(f"[Server] Connection accepted from {listener.last_accepted}")

        while True:
            try:
                msg = conn.recv()
                cmd_list = json.loads(msg)
                print(f"[Server] Received: {msg}")
                with Popen(cmd_list, stdout=PIPE, stderr=STDOUT) as p:
                    p.wait()
                    assert p.stdout
                    text = p.stdout.read()
                    #error = p.stdout.read()
                    print(f"[Server: {tid}] result: {text}")
                conn.send(f"Echo: {msg}")
            except EOFError:
                print("[Server] Connection closed by client.")
                break

        conn.close()
        listener.close()

    def stop(self):
        self._stop_event.set()


if __name__ == '__main__':
    elevate()
    root_executor = RootCommandExecutor()
    root_executor.start()
