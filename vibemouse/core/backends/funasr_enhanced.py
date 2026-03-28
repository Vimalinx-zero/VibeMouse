from __future__ import annotations

import importlib
from pathlib import Path
from threading import Lock
from typing import Protocol, cast

from vibemouse.config import AppConfig
from vibemouse.core.backends.base import (
    BackendStatus,
    BackendUnavailableError,
    HotwordList,
)


_DEFAULT_ENHANCED_MODEL = "paraformer-zh"


class FunASREnhancedBackend:
    backend_id = "funasr_enhanced"

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._model: _FunASRModel | None = None
        self._load_lock = Lock()
        self.device_in_use = _normalize_device_label(config.device)

    def availability(self) -> BackendStatus:
        try:
            _ = self._load_automodel_ctor()
        except Exception as error:
            return BackendStatus(
                backend_id=self.backend_id,
                available=False,
                reason=f"funasr dependency unavailable: {error}",
            )
        return BackendStatus(backend_id=self.backend_id, available=True)

    def prewarm(self) -> None:
        self._ensure_model_loaded()

    def transcribe(self, audio_path: Path, *, hotwords: HotwordList) -> str:
        self._ensure_model_loaded()
        if self._model is None:
            raise RuntimeError("Enhanced backend is not initialized")

        generate_kwargs: dict[str, object] = {
            "input": str(audio_path),
            "language": self._config.language,
            "use_itn": self._config.use_itn,
        }
        hotword_payload = _format_hotwords(hotwords)
        if hotword_payload:
            generate_kwargs["hotword"] = hotword_payload

        result = self._model.generate(**generate_kwargs)
        if not result:
            return ""

        first = result[0]
        if isinstance(first, dict):
            text = first.get("text", "")
        else:
            text = first
        return str(text).strip()

    def _ensure_model_loaded(self) -> None:
        if self._model is not None:
            return

        with self._load_lock:
            if self._model is not None:
                return
            AutoModel = self._load_automodel_ctor()
            try:
                self._model = AutoModel(
                    model=self._resolve_model_name(),
                    device=self.device_in_use,
                    disable_update=True,
                )
            except Exception as error:
                raise BackendUnavailableError(
                    backend_id=self.backend_id,
                    reason=f"failed to initialize model: {error}",
                ) from error

    def _resolve_model_name(self) -> str:
        current = self._config.model_name.strip()
        if current in {"", "iic/SenseVoiceSmall", "iic/SenseVoiceSmall-onnx"}:
            return _DEFAULT_ENHANCED_MODEL
        return current

    @staticmethod
    def _load_automodel_ctor() -> _AutoModelCtor:
        module = importlib.import_module("funasr")
        return cast(_AutoModelCtor, getattr(module, "AutoModel"))


def _format_hotwords(hotwords: HotwordList) -> str | None:
    if not hotwords:
        return None

    deduped: list[str] = []
    seen: set[str] = set()
    for phrase, _weight in sorted(hotwords, key=lambda item: (-item[1], item[0].casefold())):
        normalized = phrase.strip()
        key = normalized.casefold()
        if not normalized or key in seen:
            continue
        seen.add(key)
        deduped.append(normalized)

    if not deduped:
        return None
    return "\n".join(deduped)


def _normalize_device_label(device: str) -> str:
    normalized = device.strip().lower()
    if normalized.startswith("cuda"):
        return normalized
    return "cpu"


class _FunASRModel(Protocol):
    def generate(self, **kwargs: object) -> list[dict[str, object] | str]: ...


class _AutoModelCtor(Protocol):
    def __call__(self, **kwargs: object) -> _FunASRModel: ...
