from __future__ import annotations

import unittest
from types import SimpleNamespace

from vibemouse.bindings.actions import (
    build_default_bindings,
    build_resolved_bindings,
    command_for_legacy_gesture_action,
)
from vibemouse.bindings.resolver import BindingResolver
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


class BindingActionsTests(unittest.TestCase):
    @staticmethod
    def _make_config(**overrides: object) -> SimpleNamespace:
        values = {
            "bindings": {},
            "gesture_up_action": "record_toggle",
            "gesture_down_action": "noop",
            "gesture_left_action": "workspace_left",
            "gesture_right_action": "workspace_right",
            "recording_submit_keycode": 28,
        }
        values.update(overrides)
        return SimpleNamespace(**values)

    def test_default_bindings_follow_runtime_defaults(self) -> None:
        config = self._make_config()

        bindings = build_default_bindings(config)

        self.assertEqual(bindings[EVENT_MOUSE_SIDE_FRONT_PRESS], COMMAND_TOGGLE_RECORDING)
        self.assertEqual(
            bindings[EVENT_MOUSE_SIDE_REAR_PRESS],
            COMMAND_TRIGGER_SECONDARY_ACTION,
        )
        self.assertEqual(bindings[EVENT_HOTKEY_RECORD_TOGGLE], COMMAND_TOGGLE_RECORDING)
        self.assertEqual(
            bindings[EVENT_HOTKEY_RECORDING_SUBMIT],
            COMMAND_SUBMIT_RECORDING,
        )
        self.assertEqual(bindings[EVENT_GESTURE_UP], COMMAND_TOGGLE_RECORDING)
        self.assertEqual(bindings[EVENT_GESTURE_DOWN], COMMAND_NOOP)
        self.assertEqual(bindings[EVENT_GESTURE_LEFT], COMMAND_WORKSPACE_LEFT)
        self.assertEqual(bindings[EVENT_GESTURE_RIGHT], COMMAND_WORKSPACE_RIGHT)

    def test_custom_bindings_override_defaults(self) -> None:
        config = self._make_config(
            bindings={EVENT_MOUSE_SIDE_FRONT_PRESS: COMMAND_SEND_ENTER}
        )

        bindings = build_resolved_bindings(config)

        self.assertEqual(bindings[EVENT_MOUSE_SIDE_FRONT_PRESS], COMMAND_SEND_ENTER)

    def test_legacy_gesture_action_names_translate_to_commands(self) -> None:
        self.assertEqual(
            command_for_legacy_gesture_action("record_toggle"),
            COMMAND_TOGGLE_RECORDING,
        )
        self.assertEqual(
            command_for_legacy_gesture_action("workspace_right"),
            COMMAND_WORKSPACE_RIGHT,
        )
        self.assertEqual(command_for_legacy_gesture_action("noop"), COMMAND_NOOP)


class BindingResolverTests(unittest.TestCase):
    def test_resolve_returns_bound_command(self) -> None:
        resolver = BindingResolver({EVENT_MOUSE_SIDE_FRONT_PRESS: COMMAND_SEND_ENTER})

        self.assertEqual(
            resolver.resolve(EVENT_MOUSE_SIDE_FRONT_PRESS),
            COMMAND_SEND_ENTER,
        )

    def test_resolve_returns_none_for_unbound_event(self) -> None:
        resolver = BindingResolver({EVENT_MOUSE_SIDE_FRONT_PRESS: COMMAND_SEND_ENTER})

        self.assertIsNone(resolver.resolve("mouse.middle.press"))
