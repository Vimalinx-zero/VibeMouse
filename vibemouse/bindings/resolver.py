from __future__ import annotations

from collections.abc import Mapping

from vibemouse.bindings.actions import build_resolved_bindings
from vibemouse.config.schema import AppConfig


class BindingResolver:
    def __init__(self, bindings: Mapping[str, str]) -> None:
        self._bindings: dict[str, str] = {
            str(event_name).strip().lower(): str(command_name).strip().lower()
            for event_name, command_name in bindings.items()
        }

    @classmethod
    def from_config(cls, config: AppConfig) -> "BindingResolver":
        return cls(build_resolved_bindings(config))

    def resolve(self, event_name: str) -> str | None:
        normalized = event_name.strip().lower()
        if not normalized:
            return None
        return self._bindings.get(normalized)

    def snapshot(self) -> dict[str, str]:
        return dict(self._bindings)
