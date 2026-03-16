from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from vibemouse.config.env_overrides import apply_env_overrides
from vibemouse.config.schema import (
    AppConfig,
    build_default_config_document,
    config_document_to_app_config,
    default_config_path,
    default_status_file,
    default_temp_dir,
    normalize_status_document,
)
from vibemouse.config.store import ConfigStore, StatusStore, resolve_config_path


def load_config(
    config_file: str | Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> AppConfig:
    config_path = resolve_config_path(config_file)
    document = ConfigStore(config_path).load_document()
    config = config_document_to_app_config(document)
    return apply_env_overrides(config, env=env)


def write_status(path: str | Path, payload: Mapping[str, object]) -> None:
    StatusStore(Path(path)).write(payload)


__all__ = [
    "AppConfig",
    "ConfigStore",
    "StatusStore",
    "build_default_config_document",
    "config_document_to_app_config",
    "default_config_path",
    "default_status_file",
    "default_temp_dir",
    "load_config",
    "normalize_status_document",
    "resolve_config_path",
    "write_status",
]
