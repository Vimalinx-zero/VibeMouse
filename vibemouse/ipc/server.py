"""IPC server for agent to receive events from listener child via stdio (LPJSON)."""

from __future__ import annotations

import json
import logging
import struct
import threading
from typing import Any, Callable

from vibemouse.ipc.messages import (
    EventMessage,
    Message,
    _decode_lpjson,
    _encode_lpjson,
    make_command_message,
    parse_message,
)

_LOG = logging.getLogger(__name__)

_LENGTH_PREFIX_SIZE = 4
_MAX_MESSAGE_SIZE = 1024 * 1024


class IPCServer:
    """
    Server that reads events from a listener child's stdout and optionally
    sends commands to the listener's stdin.
    """

    def __init__(
        self,
        *,
        reader: Any,
        writer: Any | None = None,
        on_event: Callable[[str], None],
    ) -> None:
        self._reader = reader
        self._writer = writer
        self._on_event = on_event
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the server loop in a background thread."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the server loop."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2)

    def send_command(self, command_name: str) -> None:
        """Send a command to the listener (if writer is configured)."""
        if self._writer is None:
            return
        msg = make_command_message(command_name)
        frame = _encode_lpjson(msg)
        try:
            self._writer.write(frame)
            self._writer.flush()
        except Exception as error:
            _LOG.warning("Failed to send command to listener: %s", error)

    def _run(self) -> None:
        while self._running:
            try:
                prefix = self._reader.read(_LENGTH_PREFIX_SIZE)
                if len(prefix) == 0:
                    break
                if len(prefix) < _LENGTH_PREFIX_SIZE:
                    _LOG.warning("Truncated length prefix from listener")
                    break
                length, = struct.unpack("<I", prefix)
                if length > _MAX_MESSAGE_SIZE:
                    _LOG.error("Message size %d exceeds maximum", length)
                    break
                body = self._reader.read(length)
                if len(body) < length:
                    _LOG.warning("Truncated payload from listener")
                    break
                raw = json.loads(body.decode("utf-8"))
                msg = parse_message(raw)
                if msg.get("type") == "event":
                    event_name = msg.get("event", "")
                    self._on_event(event_name)
            except Exception as error:
                if self._running:
                    _LOG.exception("IPC server error: %s", error)
                break
        self._running = False
