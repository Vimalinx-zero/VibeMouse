"""IPC module for agent-listener communication using stdio + LPJSON."""

from vibemouse.ipc.client import IPCClient
from vibemouse.ipc.messages import (
    CommandMessage,
    EventMessage,
    Message,
    parse_message,
    serialize_message,
)
from vibemouse.ipc.server import IPCServer

__all__ = [
    "CommandMessage",
    "EventMessage",
    "IPCClient",
    "IPCServer",
    "Message",
    "parse_message",
    "serialize_message",
]
