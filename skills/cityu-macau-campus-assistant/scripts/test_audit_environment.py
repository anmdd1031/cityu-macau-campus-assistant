"""Offline regressions for audit dependency preflight."""

import unittest
from unittest.mock import patch

import audit_official_crawl as audit


class AuditEnvironmentTests(unittest.TestCase):
    def test_missing_dependency_stops_before_report(self):
        for name in ("PdfReader", "olefile", "xlrd"):
            with self.subTest(name=name), patch.object(audit, name, None):
                with patch.object(audit, "parse_args"), patch.object(
                    audit, "build_report"
                ) as build:
                    with self.assertRaisesRegex(SystemExit, "reports were not changed"):
                        audit.main()
                    build.assert_not_called()

    def test_ready_environment_passes(self):
        with patch.object(audit, "PdfReader", object()), patch.object(
            audit, "olefile", object()
        ), patch.object(audit, "xlrd", object()):
            audit.require_extraction_dependencies()


if __name__ == "__main__":
    unittest.main()
