"""Tests for IPC client-server round-trip over pipes."""

from __future__ import annotations

import io
import json
import struct
import time

from vibemouse.ipc.client import IPCClient
from vibemouse.ipc.server import IPCServer


def test_ipc_client_send_event() -> None:
    """IPCClient.send_event writes valid LPJSON to stdout (simulating pipe)."""
    stdout_buf = io.BytesIO()
    class PipeLike:
        def __init__(self, buf: io.BytesIO) -> None:
            self._buf = buf
        def write(self, data: bytes) -> int:
            return self._buf.write(data)
        def flush(self) -> None:
            pass
        @property
        def buffer(self) -> io.BytesIO:
            return self._buf
    # Actually IPCClient uses self._stdout.buffer.write - so we need stdout to have .buffer
    # For a real pipe, sys.stdout has .buffer. For test we use a wrapper.
    stdout_wrapper = PipeLike(stdout_buf)
    stdin_buf = io.BytesIO()
    stdin_wrapper = type("Stdin", (), {"buffer": stdin_buf})()
    client = IPCClient(stdin=stdin_wrapper, stdout=stdout_wrapper)
    client.send_event("hotkey.record_toggle")
    data = stdout_buf.getvalue()
    assert len(data) >= 4
    length, = struct.unpack("<I", data[:4])
    assert length == len(data) - 4
    payload = json.loads(data[4:].decode("utf-8"))
    assert payload == {"type": "event", "event": "hotkey.record_toggle"}


def test_ipc_server_receives_event() -> None:
    """IPCServer receives event from reader and calls on_event."""
    payload = {"type": "event", "event": "mouse.side_rear.press"}
    body = json.dumps(payload).encode("utf-8")
    frame = struct.pack("<I", len(body)) + body
    reader = io.BytesIO(frame)
    writer = io.BytesIO()
    received: list[str] = []
    server = IPCServer(
        reader=reader,
        writer=writer,
        on_event=lambda e: received.append(e),
    )
    server.start()
    time.sleep(0.1)
    server.stop()
    assert received == ["mouse.side_rear.press"]


def test_ipc_server_send_command() -> None:
    """IPCServer.send_command writes valid LPJSON to writer."""
    reader = io.BytesIO()  # empty, no events
    writer = io.BytesIO()
    server = IPCServer(
        reader=reader,
        writer=writer,
        on_event=lambda e: None,
    )
    server.send_command("shutdown")
    data = writer.getvalue()
    assert len(data) >= 4
    length, = struct.unpack("<I", data[:4])
    assert length == len(data) - 4
    payload = json.loads(data[4:].decode("utf-8"))
    assert payload == {"type": "command", "command": "shutdown"}
