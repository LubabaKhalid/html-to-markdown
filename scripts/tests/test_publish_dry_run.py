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


def test_node_release_builds_allow_napi_platform_regeneration() -> None:
    """The NAPI action deletes and recreates workspace platform packages."""
    workflow = yaml.safe_load((ROOT / ".github/workflows/publish.yaml").read_text())

    assert workflow["jobs"]["node-bindings"]["env"] == {"PNPM_CONFIG_FROZEN_LOCKFILE": "false"}


def test_swift_release_finalizer_refreshes_an_existing_checksum() -> None:
    """Recovery runs must replace the checksum written by an earlier build."""
    workflow = yaml.safe_load((ROOT / ".github/workflows/publish.yaml").read_text())
    steps = workflow["jobs"]["update-swift-package-manifest"]["steps"]
    tooling = next(step for step in steps if step.get("name") == "Check out release recovery tooling")
    update = next(step for step in steps if step.get("name") == "Update Package.swift with version and checksum")
    script = update["run"]

    assert tooling["with"]["ref"] == "${{ github.workflow_sha }}"
    assert tooling["with"]["path"] == ".release-tooling"
    assert 'python3 .release-tooling/scripts/ci/swift/finalize_release_manifest.py "${CHECKSUM}" "${VERSION}"' in script
