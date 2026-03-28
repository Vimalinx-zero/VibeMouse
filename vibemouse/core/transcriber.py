from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from threading import Lock

from vibemouse.config import AppConfig
from vibemouse.core.backends import (
    BackendStatus,
    BackendUnavailableError,
    FunASREnhancedBackend,
    HotwordList,
    SenseVoiceFastBackend,
    TranscriptionBackend,
)


BackendFactory = Callable[[AppConfig], TranscriptionBackend]


class SenseVoiceTranscriber:
    def __init__(
        self,
        config: AppConfig,
        *,
        backend_factories: Mapping[str, BackendFactory] | None = None,
    ) -> None:
        self._config = config
        self._backend_factories: dict[str, BackendFactory] = {
            "fast": SenseVoiceFastBackend,
            "enhanced": FunASREnhancedBackend,
        }
        if backend_factories is not None:
            self._backend_factories.update(backend_factories)

        self._backends: dict[str, TranscriptionBackend] = {}
        self._backend_lock = Lock()
        self.device_in_use = config.device
        self.backend_in_use = "unknown"
        self.profile_in_use = "unknown"

    def availability(self, *, output_target: str = "default") -> BackendStatus:
        profile = self._resolve_profile(output_target)
        return self._backend_for_profile(profile).availability()

    def transcribe(
        self,
        audio_path: Path,
        *,
        output_target: str = "default",
        hotwords: HotwordList | None = None,
    ) -> str:
        profile = self._resolve_profile(output_target)
        backend = self._backend_for_profile(profile)
        self._ensure_available(backend)
        text = backend.transcribe(audio_path, hotwords=list(hotwords or []))
        self._remember_backend(profile, backend)
        return text

    def prewarm(self, *, output_target: str = "default") -> None:
        profile = self._resolve_profile(output_target)
        backend = self._backend_for_profile(profile)
        self._ensure_available(backend)
        backend.prewarm()
        self._remember_backend(profile, backend)

    def _resolve_profile(self, output_target: str) -> str:
        normalized_target = output_target.strip().lower()
        profile = self._config.profiles.get(normalized_target)
        if profile is None:
            options = ", ".join(sorted(self._config.profiles))
            raise ValueError(
                f"output_target must be one of: {options}; got {output_target!r}"
            )
        return str(profile).strip().lower()

    def _backend_for_profile(self, profile: str) -> TranscriptionBackend:
        with self._backend_lock:
            cached = self._backends.get(profile)
            if cached is not None:
                return cached

            factory = self._backend_factories.get(profile)
            if factory is None:
                options = ", ".join(sorted(self._backend_factories))
                raise RuntimeError(
                    f"No backend factory configured for profile {profile!r}. Available: {options}"
                )

            backend = factory(self._config)
            self._backends[profile] = backend
            return backend

    @staticmethod
    def _ensure_available(backend: TranscriptionBackend) -> None:
        status = backend.availability()
        if status.available:
            return
        raise BackendUnavailableError(
            backend_id=status.backend_id,
            reason=status.reason or "backend unavailable",
        )

    def _remember_backend(self, profile: str, backend: TranscriptionBackend) -> None:
        self.profile_in_use = profile
        self.backend_in_use = backend.backend_id
        self.device_in_use = backend.device_in_use
