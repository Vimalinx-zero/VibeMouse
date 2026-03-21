from __future__ import annotations

from vibemouse.config.schema import AppConfig
from vibemouse.core.commands import (
    COMMAND_NOOP,
    COMMAND_SEND_ENTER,
    COMMAND_SUBMIT_RECORDING,
    COMMAND_TOGGLE_RECORDING,
    COMMAND_TRIGGER_SECONDARY_ACTION,
    COMMAND_WORKSPACE_LEFT,
    COMMAND_WORKSPACE_RIGHT,
    EVENT_GESTURE_DOWN,
    EVENT_GESTURE_LEFT,
    EVENT_GESTURE_RIGHT,
    EVENT_GESTURE_UP,
    EVENT_HOTKEY_RECORDING_SUBMIT,
    EVENT_HOTKEY_RECORD_TOGGLE,
    EVENT_MOUSE_SIDE_FRONT_PRESS,
    EVENT_MOUSE_SIDE_REAR_PRESS,
)


_LEGACY_GESTURE_ACTION_TO_COMMAND: dict[str, str] = {
    "noop": COMMAND_NOOP,
    "record_toggle": COMMAND_TOGGLE_RECORDING,
    "send_enter": COMMAND_SEND_ENTER,
    "workspace_left": COMMAND_WORKSPACE_LEFT,
    "workspace_right": COMMAND_WORKSPACE_RIGHT,
}


def command_for_legacy_gesture_action(action: str) -> str:
    return _LEGACY_GESTURE_ACTION_TO_COMMAND[action.strip().lower()]


def build_default_bindings(config: AppConfig) -> dict[str, str]:
    bindings = {
        EVENT_MOUSE_SIDE_FRONT_PRESS: COMMAND_TOGGLE_RECORDING,
        EVENT_MOUSE_SIDE_REAR_PRESS: COMMAND_TRIGGER_SECONDARY_ACTION,
        EVENT_HOTKEY_RECORD_TOGGLE: COMMAND_TOGGLE_RECORDING,
        EVENT_GESTURE_UP: command_for_legacy_gesture_action(config.gesture_up_action),
        EVENT_GESTURE_DOWN: command_for_legacy_gesture_action(
            config.gesture_down_action
        ),
        EVENT_GESTURE_LEFT: command_for_legacy_gesture_action(
            config.gesture_left_action
        ),
        EVENT_GESTURE_RIGHT: command_for_legacy_gesture_action(
            config.gesture_right_action
        ),
    }
    if config.recording_submit_keycode is not None:
        bindings[EVENT_HOTKEY_RECORDING_SUBMIT] = COMMAND_SUBMIT_RECORDING
    return bindings


def build_resolved_bindings(config: AppConfig) -> dict[str, str]:
    bindings = build_default_bindings(config)
    bindings.update(config.bindings)
    return bindings
