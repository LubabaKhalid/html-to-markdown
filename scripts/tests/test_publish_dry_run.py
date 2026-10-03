"""Verify source-built release packages remain buildable before registry publication."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DRY_RUN_EXPRESSION = "${{ needs.prepare.outputs.dry_run }}"


def test_source_package_builds_receive_dry_run_mode() -> None:
    """Dry runs must not resolve the unpublished workspace crate from crates.io."""
    workflow = yaml.safe_load((ROOT / ".github/workflows/publish.yaml").read_text())
    jobs = workflow["jobs"]
    build_actions = {
        "python-sdist": "xberg-io/actions/build-python-sdist@v1",
        "ruby-gem": "xberg-io/actions/build-ruby-gem@v1",
        "php-extension": "xberg-io/actions/build-php-extension@v1",
    }

    for job_name, action in build_actions.items():
        step = next(step for step in jobs[job_name]["steps"] if step.get("uses") == action)
        assert step["with"]["dry-run"] == DRY_RUN_EXPRESSION


def test_elixir_dry_run_skips_registry_dependency_rewrite() -> None:
    """Elixir dry runs must retain the workspace dependency path."""
    workflow = yaml.safe_load((ROOT / ".github/workflows/publish.yaml").read_text())
    steps = workflow["jobs"]["elixir-natives"]["steps"]
    rewrite = next(step for step in steps if step.get("uses") == "xberg-io/actions/rewrite-native-deps@v1")

    assert rewrite["if"] == "needs.prepare.outputs.dry_run != 'true'"
