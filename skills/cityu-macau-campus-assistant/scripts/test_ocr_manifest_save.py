#!/usr/bin/env python3
"""Offline regression checks for atomic OCR manifest persistence."""

from __future__ import annotations

import json
import os
import shutil
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

import ocr_official_documents as ocr


class OcrManifestSaveTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary_root = Path(__file__).resolve().parents[3] / ".cache" / "ocr-manifest-tests"
        temporary_root.mkdir(parents=True, exist_ok=True)
        self.state_dir = temporary_root / f"run-{uuid.uuid4().hex}"
        self.state_dir.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.state_dir)

    def test_transient_permission_errors_are_retried(self) -> None:
        path = self.state_dir / "manifest.json"
        real_replace = os.replace
        calls = 0

        def flaky_replace(source: Path, destination: Path) -> None:
            nonlocal calls
            calls += 1
            if calls < 3:
                raise PermissionError("synthetic Windows file lock")
            real_replace(source, destination)

        with (
            patch.object(ocr.os, "replace", side_effect=flaky_replace),
            patch.object(ocr.time, "sleep") as sleep,
        ):
            ocr.save_manifest(
                path,
                {
                    "digest": {
                        "sha256": "digest",
                        "status": "success",
                    }
                },
            )

        self.assertEqual(calls, 3)
        self.assertEqual(
            [call.args[0] for call in sleep.call_args_list],
            [0.1, 0.2],
        )
        self.assertEqual(
            json.loads(path.read_text(encoding="utf-8"))[0]["sha256"],
            "digest",
        )
        self.assertFalse(path.with_suffix(".json.tmp").exists())

    def test_persistent_permission_error_remains_terminal(self) -> None:
        path = self.state_dir / "manifest.json"
        with (
            patch.object(
                ocr.os,
                "replace",
                side_effect=PermissionError("persistent synthetic lock"),
            ) as replace,
            patch.object(ocr.time, "sleep") as sleep,
        ):
            with self.assertRaises(PermissionError):
                ocr.save_manifest(path, {})

        self.assertEqual(replace.call_count, ocr.MANIFEST_REPLACE_ATTEMPTS)
        self.assertEqual(
            sleep.call_count,
            ocr.MANIFEST_REPLACE_ATTEMPTS - 1,
        )


if __name__ == "__main__":
    unittest.main()
