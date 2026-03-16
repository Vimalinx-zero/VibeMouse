from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from vibemouse.config.migration import migrate_config_data
from vibemouse.config.schema import (
    build_default_config_document,
    default_config_path,
    normalize_config_document,
    normalize_status_document,
)


def resolve_config_path(config_file: str | Path | None = None) -> Path:
    if config_file is None:
        return default_config_path()
    return Path(config_file)


class ConfigStore:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        return self._path

    def load_document(self) -> dict[str, object]:
        if not self._path.exists():
            return build_default_config_document()

        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Invalid JSON in config file {self._path}: {error}"
            ) from error

        migrated = migrate_config_data(raw)
        return normalize_config_document(migrated)

    def save_document(self, document: Mapping[str, object]) -> None:
        normalized = normalize_config_document(document)
        _write_json_atomic(self._path, normalized)


class StatusStore:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def read_document(self) -> dict[str, object]:
        if not self._path.exists():
            return {}

        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Invalid JSON in status file {self._path}: {error}"
            ) from error

        if not isinstance(raw, dict):
            raise ValueError(f"Status file {self._path} must contain a JSON object")
        return {str(key): value for key, value in raw.items()}

    def write(self, payload: Mapping[str, object]) -> None:
        normalized = normalize_status_document(payload)
        _write_json_atomic(self._path, normalized)


def _write_json_atomic(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(path)
