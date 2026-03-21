from __future__ import annotations

import re
from typing import Final


COMMAND_NOOP: Final = "noop"
COMMAND_RELOAD_CONFIG: Final = "reload_config"
COMMAND_SEND_ENTER: Final = "send_enter"
COMMAND_SHUTDOWN: Final = "shutdown"
COMMAND_SUBMIT_RECORDING: Final = "submit_recording"
COMMAND_TOGGLE_RECORDING: Final = "toggle_recording"
COMMAND_TRIGGER_SECONDARY_ACTION: Final = "trigger_secondary_action"
COMMAND_WORKSPACE_LEFT: Final = "workspace_left"
COMMAND_WORKSPACE_RIGHT: Final = "workspace_right"

KNOWN_COMMAND_NAMES: Final[frozenset[str]] = frozenset(
    {
        COMMAND_NOOP,
        COMMAND_RELOAD_CONFIG,
        COMMAND_SEND_ENTER,
        COMMAND_SHUTDOWN,
        COMMAND_SUBMIT_RECORDING,
        COMMAND_TOGGLE_RECORDING,
        COMMAND_TRIGGER_SECONDARY_ACTION,
        COMMAND_WORKSPACE_LEFT,
        COMMAND_WORKSPACE_RIGHT,
    }
)

EVENT_GESTURE_DOWN: Final = "gesture.down"
EVENT_GESTURE_LEFT: Final = "gesture.left"
EVENT_GESTURE_RIGHT: Final = "gesture.right"
EVENT_GESTURE_UP: Final = "gesture.up"
EVENT_HOTKEY_RECORDING_SUBMIT: Final = "hotkey.recording_submit"
EVENT_HOTKEY_RECORD_TOGGLE: Final = "hotkey.record_toggle"
EVENT_MOUSE_SIDE_FRONT_PRESS: Final = "mouse.side_front.press"
EVENT_MOUSE_SIDE_REAR_PRESS: Final = "mouse.side_rear.press"

KNOWN_INPUT_EVENTS: Final[frozenset[str]] = frozenset(
    {
        EVENT_GESTURE_DOWN,
        EVENT_GESTURE_LEFT,
        EVENT_GESTURE_RIGHT,
        EVENT_GESTURE_UP,
        EVENT_HOTKEY_RECORDING_SUBMIT,
        EVENT_HOTKEY_RECORD_TOGGLE,
        EVENT_MOUSE_SIDE_FRONT_PRESS,
        EVENT_MOUSE_SIDE_REAR_PRESS,
    }
)

_EVENT_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$")


def gesture_direction_to_event(direction: str) -> str | None:
    mapping = {
        "up": EVENT_GESTURE_UP,
        "down": EVENT_GESTURE_DOWN,
        "left": EVENT_GESTURE_LEFT,
        "right": EVENT_GESTURE_RIGHT,
    }
    return mapping.get(direction.strip().lower())


def is_valid_event_name(value: str) -> bool:
    return bool(_EVENT_NAME_RE.fullmatch(value.strip().lower()))
