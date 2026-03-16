"""IPC client for connecting to agent via stdio (LPJSON)."""

from __future__ import annotations

import json
import logging
import struct
import sys
from typing import Any, Callable

from vibemouse.ipc.messages import (
    CommandMessage,
    EventMessage,
    Message,
    _decode_lpjson,
    _encode_lpjson,
    make_event_message,
    parse_message,
)

_LOG = logging.getLogger(__name__)

_LENGTH_PREFIX_SIZE = 4
_MAX_MESSAGE_SIZE = 1024 * 1024


class IPCClient:
    """
    Client that sends events to agent and receives commands from agent
    over stdio using LPJSON framing.
    """

    def __init__(
        self,
        *,
        stdin: Any = None,
        stdout: Any = None,
        on_command: Callable[[str], None] | None = None,
    ) -> None:
        self._stdin = stdin if stdin is not None else sys.stdin
        self._stdout = stdout if stdout is not None else sys.stdout
        self._on_command = on_command
        self._buffer = bytearray()
        self._running = False

    def send_event(self, event_name: str) -> None:
        """Send an event message to the agent."""
        msg = make_event_message(event_name)
        frame = _encode_lpjson(msg)
        self._stdout.buffer.write(frame)
        self._stdout.buffer.flush()

    def run(self) -> None:
        """Run the client loop: read commands from stdin, dispatch to on_command."""
        self._running = True
        while self._running:
            try:
                prefix = self._stdin.buffer.read(_LENGTH_PREFIX_SIZE)
                if len(prefix) == 0:
                    break
                if len(prefix) < _LENGTH_PREFIX_SIZE:
                    _LOG.warning("Truncated length prefix")
                    break
                length, = struct.unpack("<I", prefix)
                if length > _MAX_MESSAGE_SIZE:
                    _LOG.error("Message size %d exceeds maximum", length)
                    break
                body = self._stdin.buffer.read(length)
                if len(body) < length:
                    _LOG.warning("Truncated payload")
                    break
                raw = json.loads(body.decode("utf-8"))
                msg = parse_message(raw)
                if msg.get("type") == "command":
                    cmd = msg.get("command", "")
                    if self._on_command is not None:
                        self._on_command(cmd)
            except Exception as error:
                _LOG.exception("IPC client error: %s", error)
                break
        self._running = False

    def stop(self) -> None:
        """Stop the client loop."""
        self._running = False
