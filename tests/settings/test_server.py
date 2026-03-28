from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from urllib.request import Request, urlopen

from vibemouse.config import ConfigStore, build_default_config_document
from vibemouse.core.backends.base import BackendStatus
from vibemouse.settings.server import SettingsServer


def _request_json(
    method: str,
    url: str,
    *,
    payload: dict[str, object] | None = None,
) -> dict[str, object]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method=method)
    with urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _request_text(url: str) -> str:
    with urlopen(url, timeout=5) as response:
        return response.read().decode("utf-8")


def _request_raw(url: str) -> tuple[int, bytes]:
    with urlopen(url, timeout=5) as response:
        return response.status, response.read()


class _FakeStatusTranscriber:
    def availability(self, *, output_target: str = "default") -> BackendStatus:
        if output_target == "default":
            return BackendStatus(
                backend_id="sensevoice_fast",
                available=True,
                reason=None,
            )
        return BackendStatus(
            backend_id="funasr_enhanced",
            available=False,
            reason="funasr package is not installed",
        )


class SettingsServerTests(unittest.TestCase):
    def test_favicon_request_returns_no_content(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vibemouse-settings-") as tmp:
            config_path = Path(tmp) / "config.json"
            server = SettingsServer(config_path=config_path)
            server.start()
            try:
                status_code, body = _request_raw(f"{server.base_url}/favicon.ico")
            finally:
                server.stop()

        self.assertEqual(status_code, 204)
        self.assertEqual(body, b"")

    def test_root_serves_settings_page(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vibemouse-settings-") as tmp:
            config_path = Path(tmp) / "config.json"
            server = SettingsServer(config_path=config_path)
            server.start()
            try:
                html = _request_text(f"{server.base_url}/")
            finally:
                server.stop()

        self.assertIn("<title>VibeMouse Settings</title>", html)
        self.assertIn('id="default-profile"', html)
        self.assertIn('id="openclaw-profile"', html)
        self.assertIn('id="dictionary-table"', html)
        self.assertIn('id="backend-status"', html)

    def test_get_config_returns_profiles_and_dictionary(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vibemouse-settings-") as tmp:
            config_path = Path(tmp) / "config.json"
            document = build_default_config_document()
            document["profiles"]["default"] = "enhanced"
            document["dictionary"] = [
                {
                    "term": "Codex",
                    "phrases": ["codex", "code x"],
                    "weight": 8,
                    "scope": "both",
                    "enabled": True,
                }
            ]
            ConfigStore(config_path).save_document(document)

            server = SettingsServer(config_path=config_path)
            server.start()
            try:
                payload = _request_json("GET", f"{server.base_url}/api/config")
            finally:
                server.stop()

        self.assertEqual(payload["profiles"]["default"], "enhanced")
        self.assertEqual(payload["profiles"]["openclaw"], "enhanced")
        self.assertEqual(payload["dictionary"][0]["term"], "Codex")
        self.assertEqual(payload["dictionary"][0]["phrases"], ["codex", "code x"])

    def test_post_config_persists_updates(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vibemouse-settings-") as tmp:
            config_path = Path(tmp) / "config.json"
            server = SettingsServer(config_path=config_path)
            server.start()
            try:
                document = build_default_config_document()
                document["profiles"]["default"] = "enhanced"
                document["dictionary"] = [
                    {
                        "term": "Claude Code",
                        "phrases": ["claude code", "cloud code"],
                        "weight": 7,
                        "scope": "openclaw",
                        "enabled": True,
                    }
                ]
                payload = _request_json(
                    "POST",
                    f"{server.base_url}/api/config",
                    payload=document,
                )
            finally:
                server.stop()

            stored = ConfigStore(config_path).load_document()

        self.assertEqual(payload["profiles"]["default"], "enhanced")
        self.assertEqual(payload["dictionary"][0]["term"], "Claude Code")
        self.assertEqual(stored["profiles"]["default"], "enhanced")
        self.assertEqual(stored["dictionary"][0]["term"], "Claude Code")
        self.assertEqual(stored["dictionary"][0]["scope"], "openclaw")

    def test_get_status_returns_backend_status(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vibemouse-settings-") as tmp:
            config_path = Path(tmp) / "config.json"
            server = SettingsServer(
                config_path=config_path,
                transcriber_factory=lambda _config: _FakeStatusTranscriber(),
            )
            server.start()
            try:
                payload = _request_json("GET", f"{server.base_url}/api/status")
            finally:
                server.stop()

        self.assertEqual(payload["backends"]["default"]["backend_id"], "sensevoice_fast")
        self.assertTrue(payload["backends"]["default"]["available"])
        self.assertEqual(
            payload["backends"]["openclaw"]["backend_id"],
            "funasr_enhanced",
        )
        self.assertFalse(payload["backends"]["openclaw"]["available"])
        self.assertEqual(
            payload["backends"]["openclaw"]["reason"],
            "funasr package is not installed",
        )
