from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


HotwordList = list[tuple[str, int]]


@dataclass(frozen=True)
class BackendStatus:
    backend_id: str
    available: bool
    reason: str | None = None


class BackendUnavailableError(RuntimeError):
    def __init__(self, *, backend_id: str, reason: str) -> None:
        self.backend_id = backend_id
        self.reason = reason
        super().__init__(f"{backend_id} unavailable: {reason}")


class TranscriptionBackend(Protocol):
    backend_id: str
    device_in_use: str

    def availability(self) -> BackendStatus: ...

    def prewarm(self) -> None: ...

    def transcribe(self, audio_path: Path, *, hotwords: HotwordList) -> str: ...
