"""Fail CI when poly reports an unsuppressed quality warning."""

import json
import subprocess
from unittest.mock import Mock

import check_quality_warnings
import pytest


def _poly_result(payload: dict[str, object], returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["poly"], returncode, stdout=json.dumps(payload), stderr="poly stderr")


def _git_result(*paths: str, returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        ["git"], returncode, stdout="".join(f"{path}\n" for path in paths), stderr="git stderr"
    )


def test_quality_warning_fails_with_its_location(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    payload = {
        "results": [
            {
                "path": "src/renamed.rs",
                "diagnostics": [
                    {
                        "engine": "quality",
                        "severity": "warning",
                        "code": "function-too-long",
                        "title": "function is 94 lines (max 80)",
                        "span": {"start_line": 27, "start_col": 1},
                    },
                    {"engine": "ruff", "severity": "warning", "code": "E501", "title": "line too long"},
                ],
            }
        ]
    }
    run = Mock(side_effect=[_git_result("scripts/check_quality_warnings.py"), _poly_result(payload)])
    monkeypatch.setattr(check_quality_warnings.subprocess, "run", run)

    assert check_quality_warnings.main() == 1
    assert capsys.readouterr().err == (
        "src/renamed.rs:27:1: quality/function-too-long: function is 94 lines (max 80)\n"
    )


def test_no_quality_warning_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {"results": [], "errors": [], "summary": {"checked": 1}}
    run = Mock(side_effect=[_git_result("scripts/check_quality_warnings.py"), _poly_result(payload)])
    monkeypatch.setattr(check_quality_warnings.subprocess, "run", run)

    assert check_quality_warnings.main() == 0


def test_poly_failure_is_not_hidden(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    run = Mock(side_effect=[_git_result("scripts/check_quality_warnings.py"), _poly_result({}, returncode=2)])
    monkeypatch.setattr(check_quality_warnings.subprocess, "run", run)

    assert check_quality_warnings.main() == 2
    assert capsys.readouterr().err == "poly stderr"
