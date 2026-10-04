#!/usr/bin/env python3
"""Fail when poly reports an unsuppressed quality warning."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPO_WIDE_QUALITY_CONFIGS = {"alef.toml", "poly.toml"}


def _quality_warnings(payload: dict[str, Any]) -> list[tuple[tuple[str, str], str]]:
    warnings = []
    for result in payload.get("results", []):
        path = result["path"]
        for diagnostic in result.get("diagnostics", []):
            if diagnostic.get("engine") != "quality" or diagnostic.get("severity") != "warning":
                continue
            span = diagnostic.get("span", {})
            line = span.get("start_line", 1)
            column = span.get("start_col", 1)
            code = diagnostic["code"]
            message = f"{path}:{line}:{column}: quality/{code}: {diagnostic['title']}"
            warnings.append(((path, code), message))
    return warnings


def _new_quality_warnings(head: dict[str, Any], baseline: dict[str, Any]) -> list[str]:
    baseline_counts = Counter(key for key, _message in _quality_warnings(baseline))
    warnings = []
    for key, message in _quality_warnings(head):
        if baseline_counts[key] > 0:
            baseline_counts[key] -= 1
        else:
            warnings.append(message)
    return warnings


def _poly_payload(root: Path, paths: list[str]) -> tuple[int, dict[str, Any] | None]:
    result = subprocess.run(
        ["poly", "lint", *paths, "--format", "json", "--no-workspace"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr, end="")
        return result.returncode, None
    try:
        return 0, json.loads(result.stdout)
    except json.JSONDecodeError as error:
        print(f"invalid poly JSON: {error}", file=sys.stderr)
        return 2, None


def _baseline_payload(base: str, paths: list[str]) -> tuple[int, dict[str, Any] | None]:
    with tempfile.TemporaryDirectory(prefix="html-to-markdown-quality-") as temp_dir:
        temp_root = Path(temp_dir)
        archive = temp_root / "baseline.tar"
        baseline_root = temp_root / "tree"
        baseline_root.mkdir()
        archived = subprocess.run(
            ["git", "archive", "--format=tar", "--output", str(archive), base],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if archived.returncode != 0:
            print(archived.stderr, file=sys.stderr, end="")
            return archived.returncode, None
        try:
            shutil.unpack_archive(archive, baseline_root, format="tar")
        except (OSError, shutil.ReadError, ValueError) as error:
            print(f"cannot extract quality baseline: {error}", file=sys.stderr)
            return 2, None
        baseline_paths = paths if paths == ["."] else [path for path in paths if (baseline_root / path).is_file()]
        if not baseline_paths:
            return 0, {"results": []}
        return _poly_payload(baseline_root, baseline_paths)


def main() -> int:
    base = os.environ.get("QUALITY_BASE") or "HEAD^"
    changed = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base}...HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if changed.returncode != 0:
        print(changed.stderr, file=sys.stderr, end="")
        return changed.returncode
    paths = [path for path in changed.stdout.splitlines() if (ROOT / path).is_file()]
    if not paths:
        return 0
    lint_paths = ["."] if REPO_WIDE_QUALITY_CONFIGS.intersection(paths) else paths
    head_code, head_payload = _poly_payload(ROOT, lint_paths)
    if head_code != 0 or head_payload is None:
        return head_code
    baseline_code, baseline_payload = _baseline_payload(base, lint_paths)
    if baseline_code != 0 or baseline_payload is None:
        return baseline_code
    warnings = _new_quality_warnings(head_payload, baseline_payload)
    for warning in warnings:
        print(warning, file=sys.stderr)
    return 1 if warnings else 0


if __name__ == "__main__":
    sys.exit(main())
