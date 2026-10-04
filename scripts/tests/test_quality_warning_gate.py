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
    monkeypatch.setattr(check_quality_warnings, "_baseline_payload", Mock(return_value=(0, {"results": []})))

    assert check_quality_warnings.main() == 1
    assert capsys.readouterr().err == (
        "src/renamed.rs:27:1: quality/function-too-long: function is 94 lines (max 80)\n"
    )


def test_no_quality_warning_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {"results": [], "errors": [], "summary": {"checked": 1}}
    run = Mock(side_effect=[_git_result("scripts/check_quality_warnings.py"), _poly_result(payload)])
    monkeypatch.setattr(check_quality_warnings.subprocess, "run", run)
    monkeypatch.setattr(check_quality_warnings, "_baseline_payload", Mock(return_value=(0, {"results": []})))

    assert check_quality_warnings.main() == 0


def test_preexisting_quality_warning_does_not_fail_when_measurement_moves() -> None:
    baseline = {
        "results": [
            {
                "path": "src/converter.rs",
                "diagnostics": [
                    {
                        "engine": "quality",
                        "severity": "warning",
                        "code": "file-too-long",
                        "title": "file is 1100 lines (max 1000)",
                        "span": {"start_line": 1, "start_col": 1},
                    }
                ],
            }
        ]
    }
    head = {
        "results": [
            {
                "path": "src/converter.rs",
                "diagnostics": [
                    {
                        "engine": "quality",
                        "severity": "warning",
                        "code": "file-too-long",
                        "title": "file is 1137 lines (max 1000)",
                        "span": {"start_line": 1, "start_col": 1},
                    }
                ],
            }
        ]
    }

    assert check_quality_warnings._new_quality_warnings(head, baseline) == []


def test_new_quality_warning_fails_after_baseline_comparison() -> None:
    head = {
        "results": [
            {
                "path": "src/converter.rs",
                "diagnostics": [
                    {
                        "engine": "quality",
                        "severity": "warning",
                        "code": "nesting-too-deep",
                        "title": "nesting depth is 5 (max 4)",
                        "span": {"start_line": 42, "start_col": 9},
                    }
                ],
            }
        ]
    }

    assert check_quality_warnings._new_quality_warnings(head, {"results": []}) == [
        "src/converter.rs:42:9: quality/nesting-too-deep: nesting depth is 5 (max 4)"
    ]


def test_additional_occurrence_of_existing_rule_fails() -> None:
    baseline_diagnostic = {
        "engine": "quality",
        "severity": "warning",
        "code": "nesting-too-deep",
        "title": "nesting depth is 5 (max 4)",
        "span": {"start_line": 10, "start_col": 5},
    }
    new_diagnostic = {
        **baseline_diagnostic,
        "span": {"start_line": 42, "start_col": 9},
    }
    baseline = {"results": [{"path": "src/converter.rs", "diagnostics": [baseline_diagnostic]}]}
    head = {"results": [{"path": "src/converter.rs", "diagnostics": [baseline_diagnostic, new_diagnostic]}]}

    assert check_quality_warnings._new_quality_warnings(head, baseline) == [
        "src/converter.rs:42:9: quality/nesting-too-deep: nesting depth is 5 (max 4)"
    ]


def test_baseline_only_change_scans_unchanged_source_files(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "results": [
            {
                "path": "crates/html-to-markdown/src/lib.rs",
                "diagnostics": [
                    {
                        "engine": "quality",
                        "severity": "warning",
                        "code": "file-too-long",
                        "title": "file is 801 lines (max 800)",
                    }
                ],
            }
        ]
    }
    run = Mock(side_effect=[_git_result("alef.toml"), _poly_result(payload)])
    monkeypatch.setattr(check_quality_warnings.subprocess, "run", run)
    baseline = Mock(return_value=(0, {"results": []}))
    monkeypatch.setattr(check_quality_warnings, "_baseline_payload", baseline)

    assert check_quality_warnings.main() == 1
    assert run.call_args_list[1].args[0] == ["poly", "lint", ".", "--format", "json", "--no-workspace"]
    assert baseline.call_args.args == ("HEAD^", ["."])


def test_poly_failure_is_not_hidden(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    run = Mock(side_effect=[_git_result("scripts/check_quality_warnings.py"), _poly_result({}, returncode=2)])
    monkeypatch.setattr(check_quality_warnings.subprocess, "run", run)

    assert check_quality_warnings.main() == 2
    assert capsys.readouterr().err == "poly stderr"
