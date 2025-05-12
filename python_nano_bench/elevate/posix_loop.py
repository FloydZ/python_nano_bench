#!/usr/bin/env python3

from multiprocessing.connection import Listener
import threading
import time
import os

import queue
from subprocess import Popen, PIPE, STDOUT

from . import posix

ADDRESS = ('localhost', 6000)
AUTHKEY = b'secret'


class RootCommandExecutor(threading.Thread):
    """
    this class spawns a additional shell with root rights, and then forwards
    commands to this shell
    """
    def __init__(self, 
                 cmd_queue,
                 response_dict: dict) -> None:
        super().__init__(daemon=True, name="RootCommandExecutor")
        self._queue = cmd_queue
        self._stop_event = threading.Event()
        self.response_dict = response_dict

    def run(self):
        """
        TODO
        """
        tid = threading.get_native_id()
        print(f"[RootCommandExecutor: {tid}] elevating rights")
        assert os.getuid() == 0
        
        print(f"[RootCommandExecutor: {tid}] start loop")
        while not self._stop_event.is_set():
            try:
                request_id, cmd_list, event = self._queue.get(timeout=1)
                print(f"[RootCommandExecutor: {tid}] Executing: {' '.join(cmd_list)}")
                with Popen(cmd_list, stdout=PIPE, stderr=STDOUT) as p:
                    p.wait()
                    assert p.stdout
                    text = p.stdout.read()
                    error = p.stdout.read()
                    print(f"[RootCommandExecutor: {tid}] result: {text}")
                    self.response_dict[request_id] = (text, error)
                event.set()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[RootCommandExecutor: {tid}] Exception: {e}")

    def stop(self):
        self._stop_event.set()


def main():
    posix.elevate()
    listener = Listener(ADDRESS, authkey=AUTHKEY)
    print(f"[Server] Listening on {ADDRESS}...")

    conn = listener.accept()
    print(f"[Server] Connection accepted from {listener.last_accepted}")

    while True:
        try:
            msg = conn.recv()
            if msg == 'exit':
                print("[Server] Exit command received. Shutting down.")
                break
            print(f"[Server] Received: {msg}")
            conn.send(f"Echo: {msg}")
        except EOFError:
            print("[Server] Connection closed by client.")
            break

    conn.close()
    listener.close()


if __name__ == '__main__':
    main()
