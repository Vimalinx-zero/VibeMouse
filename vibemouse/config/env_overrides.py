from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path

from vibemouse.config.schema import AppConfig


def apply_env_overrides(
    config: AppConfig,
    *,
    env: Mapping[str, str] | None = None,
) -> AppConfig:
    source = env if env is not None else os.environ

    sample_rate = _require_positive(
        "VIBEMOUSE_SAMPLE_RATE",
        _read_int(source, "VIBEMOUSE_SAMPLE_RATE", config.sample_rate),
    )
    channels = _require_positive(
        "VIBEMOUSE_CHANNELS",
        _read_int(source, "VIBEMOUSE_CHANNELS", config.channels),
    )
    vad_max_segment_ms = _require_positive(
        "VIBEMOUSE_VAD_MAX_SEGMENT_MS",
        _read_int(
            source,
            "VIBEMOUSE_VAD_MAX_SEGMENT_MS",
            config.vad_max_single_segment_ms,
        ),
    )
    merge_length_s = _require_positive(
        "VIBEMOUSE_MERGE_LENGTH_S",
        _read_int(source, "VIBEMOUSE_MERGE_LENGTH_S", config.merge_length_s),
    )
    front_button = _read_button(source, "VIBEMOUSE_FRONT_BUTTON", config.front_button)
    rear_button = _read_button(source, "VIBEMOUSE_REAR_BUTTON", config.rear_button)
    if front_button == rear_button:
        raise ValueError("VIBEMOUSE_FRONT_BUTTON and VIBEMOUSE_REAR_BUTTON must differ")

    default_hotkeys = tuple(config.record_hotkey_keycodes)
    if len(default_hotkeys) != 3:
        raise ValueError("record_hotkey_keycodes must contain exactly three values")
    record_hotkey_keycodes = tuple(
        sorted(
            {
                _require_non_negative(
                    "VIBEMOUSE_RECORD_HOTKEY_CODE_1",
                    _read_int(
                        source,
                        "VIBEMOUSE_RECORD_HOTKEY_CODE_1",
                        default_hotkeys[0],
                    ),
                ),
                _require_non_negative(
                    "VIBEMOUSE_RECORD_HOTKEY_CODE_2",
                    _read_int(
                        source,
                        "VIBEMOUSE_RECORD_HOTKEY_CODE_2",
                        default_hotkeys[1],
                    ),
                ),
                _require_non_negative(
                    "VIBEMOUSE_RECORD_HOTKEY_CODE_3",
                    _read_int(
                        source,
                        "VIBEMOUSE_RECORD_HOTKEY_CODE_3",
                        default_hotkeys[2],
                    ),
                ),
            }
        )
    )
    if len(record_hotkey_keycodes) != 3:
        raise ValueError("VIBEMOUSE_RECORD_HOTKEY_CODE_1/2/3 must be distinct")

    recording_submit_keycode = _read_optional_int(
        source,
        "VIBEMOUSE_RECORDING_SUBMIT_KEYCODE",
        config.recording_submit_keycode,
    )
    if recording_submit_keycode is not None:
        recording_submit_keycode = _require_non_negative(
            "VIBEMOUSE_RECORDING_SUBMIT_KEYCODE",
            recording_submit_keycode,
        )

    button_debounce_ms = _require_non_negative(
        "VIBEMOUSE_BUTTON_DEBOUNCE_MS",
        _read_int(source, "VIBEMOUSE_BUTTON_DEBOUNCE_MS", config.button_debounce_ms),
    )
    gesture_trigger_button = _read_choice(
        source,
        "VIBEMOUSE_GESTURE_TRIGGER_BUTTON",
        config.gesture_trigger_button,
        {"front", "rear", "right"},
    )
    gesture_threshold_px = _require_positive(
        "VIBEMOUSE_GESTURE_THRESHOLD_PX",
        _read_int(
            source,
            "VIBEMOUSE_GESTURE_THRESHOLD_PX",
            config.gesture_threshold_px,
        ),
    )
    gesture_actions = {
        "record_toggle",
        "send_enter",
        "workspace_left",
        "workspace_right",
        "noop",
    }
    gesture_up_action = _read_choice(
        source,
        "VIBEMOUSE_GESTURE_UP_ACTION",
        config.gesture_up_action,
        gesture_actions,
    )
    gesture_down_action = _read_choice(
        source,
        "VIBEMOUSE_GESTURE_DOWN_ACTION",
        config.gesture_down_action,
        gesture_actions,
    )
    gesture_left_action = _read_choice(
        source,
        "VIBEMOUSE_GESTURE_LEFT_ACTION",
        config.gesture_left_action,
        gesture_actions,
    )
    gesture_right_action = _read_choice(
        source,
        "VIBEMOUSE_GESTURE_RIGHT_ACTION",
        config.gesture_right_action,
        gesture_actions,
    )
    enter_mode = _read_choice(
        source,
        "VIBEMOUSE_ENTER_MODE",
        config.enter_mode,
        {"enter", "ctrl_enter", "shift_enter", "none"},
    )
    openclaw_command = source.get(
        "VIBEMOUSE_OPENCLAW_COMMAND",
        config.openclaw_command,
    ).strip()
    if not openclaw_command:
        raise ValueError("VIBEMOUSE_OPENCLAW_COMMAND must not be empty")
    openclaw_agent = source.get(
        "VIBEMOUSE_OPENCLAW_AGENT",
        "" if config.openclaw_agent is None else config.openclaw_agent,
    ).strip()
    prewarm_delay_s = _require_non_negative_float(
        "VIBEMOUSE_PREWARM_DELAY_S",
        _read_float(source, "VIBEMOUSE_PREWARM_DELAY_S", config.prewarm_delay_s),
    )

    return replace(
        config,
        sample_rate=sample_rate,
        channels=channels,
        dtype=source.get("VIBEMOUSE_DTYPE", config.dtype).strip() or config.dtype,
        transcriber_backend=source.get(
            "VIBEMOUSE_BACKEND",
            config.transcriber_backend,
        )
        .strip()
        .lower(),
        model_name=source.get("VIBEMOUSE_MODEL", config.model_name).strip()
        or config.model_name,
        log_level=_read_choice(
            source,
            "VIBEMOUSE_LOG_LEVEL",
            config.log_level.lower(),
            {"debug", "info", "warning", "error", "critical"},
        ).upper(),
        device=source.get("VIBEMOUSE_DEVICE", config.device).strip() or config.device,
        language=source.get("VIBEMOUSE_LANGUAGE", config.language).strip()
        or config.language,
        use_itn=_read_bool(source, "VIBEMOUSE_USE_ITN", config.use_itn),
        enable_vad=_read_bool(source, "VIBEMOUSE_ENABLE_VAD", config.enable_vad),
        vad_max_single_segment_ms=vad_max_segment_ms,
        merge_vad=_read_bool(source, "VIBEMOUSE_MERGE_VAD", config.merge_vad),
        merge_length_s=merge_length_s,
        fallback_to_cpu=_read_bool(
            source,
            "VIBEMOUSE_FALLBACK_CPU",
            config.fallback_to_cpu,
        ),
        button_debounce_ms=button_debounce_ms,
        gestures_enabled=_read_bool(
            source,
            "VIBEMOUSE_GESTURES_ENABLED",
            config.gestures_enabled,
        ),
        gesture_trigger_button=gesture_trigger_button,
        gesture_threshold_px=gesture_threshold_px,
        gesture_freeze_pointer=_read_bool(
            source,
            "VIBEMOUSE_GESTURE_FREEZE_POINTER",
            config.gesture_freeze_pointer,
        ),
        gesture_restore_cursor=_read_bool(
            source,
            "VIBEMOUSE_GESTURE_RESTORE_CURSOR",
            config.gesture_restore_cursor,
        ),
        gesture_up_action=gesture_up_action,
        gesture_down_action=gesture_down_action,
        gesture_left_action=gesture_left_action,
        gesture_right_action=gesture_right_action,
        enter_mode=enter_mode,
        auto_paste=_read_bool(source, "VIBEMOUSE_AUTO_PASTE", config.auto_paste),
        trust_remote_code=_read_bool(
            source,
            "VIBEMOUSE_TRUST_REMOTE_CODE",
            config.trust_remote_code,
        ),
        prewarm_on_start=_read_bool(
            source,
            "VIBEMOUSE_PREWARM_ON_START",
            config.prewarm_on_start,
        ),
        prewarm_delay_s=prewarm_delay_s,
        status_file=_read_path(source, "VIBEMOUSE_STATUS_FILE", config.status_file),
        openclaw_command=openclaw_command,
        openclaw_agent=openclaw_agent or None,
        openclaw_timeout_s=_require_positive_float(
            "VIBEMOUSE_OPENCLAW_TIMEOUT_S",
            _read_float(
                source,
                "VIBEMOUSE_OPENCLAW_TIMEOUT_S",
                config.openclaw_timeout_s,
            ),
        ),
        openclaw_retries=_require_non_negative(
            "VIBEMOUSE_OPENCLAW_RETRIES",
            _read_int(source, "VIBEMOUSE_OPENCLAW_RETRIES", config.openclaw_retries),
        ),
        front_button=front_button,
        rear_button=rear_button,
        record_hotkey_keycodes=record_hotkey_keycodes,
        recording_submit_keycode=recording_submit_keycode,
        temp_dir=_read_path(source, "VIBEMOUSE_TEMP_DIR", config.temp_dir),
    )


def _read_bool(source: Mapping[str, str], name: str, default: bool) -> bool:
    raw = source.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _read_int(source: Mapping[str, str], name: str, default: int) -> int:
    raw = source.get(name)
    if raw is None:
        return default
    try:
        return int(raw.strip())
    except ValueError as error:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from error


def _read_optional_int(
    source: Mapping[str, str],
    name: str,
    default: int | None,
) -> int | None:
    raw = source.get(name)
    if raw is None:
        return default
    normalized = raw.strip()
    if not normalized:
        return None
    try:
        return int(normalized)
    except ValueError as error:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from error


def _read_float(source: Mapping[str, str], name: str, default: float) -> float:
    raw = source.get(name)
    if raw is None:
        return default
    try:
        return float(raw.strip())
    except ValueError as error:
        raise ValueError(f"{name} must be a float, got {raw!r}") from error


def _read_button(source: Mapping[str, str], name: str, default: str) -> str:
    value = source.get(name, default).strip().lower()
    if value not in {"x1", "x2"}:
        raise ValueError(f"{name} must be either 'x1' or 'x2', got {value!r}")
    return value


def _read_choice(
    source: Mapping[str, str],
    name: str,
    default: str,
    allowed: set[str],
) -> str:
    value = source.get(name, default).strip().lower()
    if value not in allowed:
        options = ", ".join(sorted(allowed))
        raise ValueError(f"{name} must be one of: {options}; got {value!r}")
    return value


def _read_path(source: Mapping[str, str], name: str, default: Path) -> Path:
    raw = source.get(name)
    if raw is None:
        return default
    return Path(raw)


def _require_positive(name: str, value: int) -> int:
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer, got {value}")
    return value


def _require_non_negative(name: str, value: int) -> int:
    if value < 0:
        raise ValueError(f"{name} must be a non-negative integer, got {value}")
    return value


def _require_positive_float(name: str, value: float) -> float:
    if value <= 0:
        raise ValueError(f"{name} must be a positive float, got {value}")
    return value


def _require_non_negative_float(name: str, value: float) -> float:
    if value < 0:
        raise ValueError(f"{name} must be a non-negative float, got {value}")
    return value
