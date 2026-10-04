"""Verify workflow triggers and concurrency preserve required CI checks."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _workflow(name: str) -> dict[str, object]:
    source = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
    return yaml.safe_load(source.replace("\non:\n", '\n"on":\n', 1))


def test_docs_pushes_use_commit_specific_concurrency_groups() -> None:
    workflow = _workflow("ci-docs.yaml")

    assert workflow["concurrency"] == {
        "group": "ci-docs-${{ github.event.pull_request.number || github.sha }}",
        "cancel-in-progress": False,
    }


def test_r_configure_changes_start_lint_for_pushes_and_pull_requests() -> None:
    workflow = _workflow("ci-lint.yaml")

    for event in ("push", "pull_request"):
        assert "packages/r/configure" in workflow["on"][event]["paths"]
