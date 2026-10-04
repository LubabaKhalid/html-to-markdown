#!/usr/bin/env python3
"""Fail when poly reports an unsuppressed quality warning."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _quality_warnings(payload: dict[str, Any]) -> list[str]:
    warnings = []
    for result in payload.get("results", []):
        path = result["path"]
        for diagnostic in result.get("diagnostics", []):
            if diagnostic.get("engine") != "quality" or diagnostic.get("severity") != "warning":
                continue
            span = diagnostic.get("span", {})
            line = span.get("start_line", 1)
            column = span.get("start_col", 1)
            warnings.append(f"{path}:{line}:{column}: quality/{diagnostic['code']}: {diagnostic['title']}")
    return warnings


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
    result = subprocess.run(
        ["poly", "lint", *paths, "--format", "json", "--no-workspace"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr, end="")
        return result.returncode
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        print(f"invalid poly JSON: {error}", file=sys.stderr)
        return 2
    warnings = _quality_warnings(payload)
    for warning in warnings:
        print(warning, file=sys.stderr)
    return 1 if warnings else 0


if __name__ == "__main__":
    sys.exit(main())
