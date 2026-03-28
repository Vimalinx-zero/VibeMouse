from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from vibemouse.config import (
    build_default_config_document,
    config_document_to_app_config,
)
from vibemouse.core.backends.base import BackendStatus


def _load_eval_module():
    module_path = (
        Path(__file__).resolve().parents[2] / "scripts" / "eval_dictation_profiles.py"
    )
    spec = importlib.util.spec_from_file_location(
        "eval_dictation_profiles",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class _AvailableFakeTranscriber:
    def __init__(self, config) -> None:
        self._config = config

    def availability(self, *, output_target: str = "default") -> BackendStatus:
        profile = self._config.profiles[output_target]
        if profile == "fast":
            return BackendStatus(
                backend_id="sensevoice_fast",
                available=True,
                reason=None,
            )
        return BackendStatus(
            backend_id="funasr_enhanced",
            available=True,
            reason=None,
        )

    def transcribe(self, audio_path: Path, *, output_target: str = "default", hotwords=None):
        profile = self._config.profiles[output_target]
        outputs = {
            "fast": {
                "sample-1.wav": "ask code x to review",
                "sample-2.wav": "open codex right now",
            },
            "enhanced": {
                "sample-1.wav": "ask codex to review",
                "sample-2.wav": "open codex now",
            },
        }
        return outputs[profile][audio_path.name]


class _UnavailableEnhancedTranscriber:
    def __init__(self, config) -> None:
        self._config = config

    def availability(self, *, output_target: str = "default") -> BackendStatus:
        profile = self._config.profiles[output_target]
        if profile == "enhanced":
            return BackendStatus(
                backend_id="funasr_enhanced",
                available=False,
                reason="funasr package is not installed",
            )
        return BackendStatus(
            backend_id="sensevoice_fast",
            available=True,
            reason=None,
        )

    def transcribe(self, audio_path: Path, *, output_target: str = "default", hotwords=None):
        return {
            "sample-1.wav": "ask code x to review",
            "sample-2.wav": "open codex right now",
        }[audio_path.name]


class DictationProfileEvalScriptTests(unittest.TestCase):
    def test_eval_script_help_runs_as_cli_from_repo_root(self) -> None:
        script_path = Path(__file__).resolve().parents[2] / "scripts" / "eval_dictation_profiles.py"
        project_root = Path(__file__).resolve().parents[2]

        completed = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            cwd=project_root,
            env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("usage:", completed.stdout)

    def test_eval_script_scores_term_hits_and_exact_matches(self) -> None:
        module = _load_eval_module()
        config_document = build_default_config_document()
        config_document["dictionary"] = [
            {
                "term": "Codex",
                "phrases": ["codex", "code x"],
                "weight": 8,
                "scope": "both",
                "enabled": True,
            }
        ]
        config = config_document_to_app_config(config_document)

        with tempfile.TemporaryDirectory(prefix="vibemouse-eval-") as tmp:
            dataset_path = Path(tmp) / "eval.jsonl"
            dataset_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "audio_path": "sample-1.wav",
                                "output_target": "default",
                                "reference_text": "ask Codex to review",
                                "expected_terms": ["Codex"],
                            }
                        ),
                        json.dumps(
                            {
                                "audio_path": "sample-2.wav",
                                "output_target": "default",
                                "reference_text": "open Codex now",
                                "expected_terms": ["Codex"],
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = module.evaluate_dataset(
                dataset_path,
                config,
                transcriber_factory=_AvailableFakeTranscriber,
            )

        fast = report["profiles"]["fast"]
        enhanced = report["profiles"]["enhanced"]

        self.assertEqual(report["dataset_size"], 2)
        self.assertEqual(fast["backend_id"], "sensevoice_fast")
        self.assertEqual(fast["transcribed_records"], 2)
        self.assertEqual(fast["exact_matches"], 1)
        self.assertEqual(fast["term_hits"], 2)
        self.assertEqual(fast["term_total"], 2)
        self.assertAlmostEqual(fast["exact_match_rate"], 0.5)
        self.assertAlmostEqual(fast["term_hit_rate"], 1.0)
        self.assertEqual(enhanced["backend_id"], "funasr_enhanced")
        self.assertEqual(enhanced["transcribed_records"], 2)
        self.assertEqual(enhanced["exact_matches"], 2)
        self.assertEqual(enhanced["term_hits"], 2)
        self.assertEqual(enhanced["term_total"], 2)
        self.assertAlmostEqual(enhanced["exact_match_rate"], 1.0)
        self.assertAlmostEqual(enhanced["term_hit_rate"], 1.0)

    def test_eval_script_reports_backend_unavailability(self) -> None:
        module = _load_eval_module()
        config_document = build_default_config_document()
        config_document["dictionary"] = [
            {
                "term": "Codex",
                "phrases": ["codex", "code x"],
                "weight": 8,
                "scope": "both",
                "enabled": True,
            }
        ]
        config = config_document_to_app_config(config_document)

        with tempfile.TemporaryDirectory(prefix="vibemouse-eval-") as tmp:
            dataset_path = Path(tmp) / "eval.jsonl"
            dataset_path.write_text(
                json.dumps(
                    {
                        "audio_path": "sample-1.wav",
                        "output_target": "default",
                        "reference_text": "ask Codex to review",
                        "expected_terms": ["Codex"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            report = module.evaluate_dataset(
                dataset_path,
                config,
                transcriber_factory=_UnavailableEnhancedTranscriber,
            )

        fast = report["profiles"]["fast"]
        enhanced = report["profiles"]["enhanced"]

        self.assertEqual(fast["transcribed_records"], 1)
        self.assertEqual(fast["unavailable_records"], 0)
        self.assertEqual(enhanced["transcribed_records"], 0)
        self.assertEqual(enhanced["unavailable_records"], 1)
        self.assertEqual(
            enhanced["unavailable_reasons"],
            ["funasr package is not installed"],
        )
