"""Keep every gated E2E job's path filters aligned with the inputs it reads."""

import copy
import re
import tomllib
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "ci-e2e.yaml"
ALEF_PATH = ROOT / "alef.toml"
OUTPUT_FILTER = re.compile(r"steps\.filter\.outputs\.([a-z]+) == 'true'")
ALEF_LANGUAGE = re.compile(r"alef test --e2e --lang ([a-z_]+)")
CARGO_PACKAGE = re.compile(r"(?:^|\s)-p\s+([a-z0-9_-]+)")
SCRIPT_PATH = re.compile(r"(?:^|[\s\"'])(scripts/[A-Za-z0-9_./-]+)")
CHANGE_DIRECTORY = re.compile(r"(?:^|&&|;)\s*cd\s+([^\s;&]+)")


def _cargo_packages() -> dict[str, str]:
    packages = {}
    for pattern in ("crates/*/Cargo.toml", "packages/**/Cargo.toml"):
        for manifest in ROOT.glob(pattern):
            package = tomllib.loads(manifest.read_text(encoding="utf-8"))["package"]["name"]
            packages[package] = manifest.parent.relative_to(ROOT).as_posix()
    return packages


def _filter_step(workflow: dict[str, Any]) -> dict[str, Any]:
    (step,) = [step for step in workflow["jobs"]["changes"]["steps"] if step.get("id") == "filter"]
    return step


def _commands(job: dict[str, Any], alef: dict[str, Any]) -> list[str]:
    commands = [str(step.get("run", "")) for step in job.get("steps", [])]
    languages = {language for command in commands for language in ALEF_LANGUAGE.findall(command)}
    for language in languages:
        test = alef["crates"][0]["test"][language]
        commands.extend(str(test.get(key, "")) for key in ("before", "e2e"))
    return commands


def _job_inputs(job: dict[str, Any], alef: dict[str, Any], packages: dict[str, str]) -> set[str]:
    inputs = {".github/workflows/ci-e2e.yaml"}
    commands = _commands(job, alef)
    if any(ALEF_LANGUAGE.search(command) for command in commands):
        inputs.add("alef.toml")
    for step in job.get("steps", []):
        if directory := step.get("working-directory"):
            inputs.add(str(directory))
        options = step.get("with", {})
        if directory := options.get("crate-dir"):
            inputs.add(str(directory))
        for key in ("crate-name", "ffi-crate-name"):
            if package := options.get(key):
                inputs.add(packages[str(package)])
    for command in commands:
        inputs.update(SCRIPT_PATH.findall(command))
        inputs.update(
            path.strip("'\"")
            for path in CHANGE_DIRECTORY.findall(command)
            if path.startswith(("crates/", "packages/", "e2e/", "scripts/"))
        )
        inputs.update(packages[package] for package in CARGO_PACKAGE.findall(command))
    return inputs


def _covered(path: str, patterns: set[str]) -> bool:
    return any(
        pattern == path or (pattern.endswith("/**") and (path == pattern[:-3] or path.startswith(f"{pattern[:-3]}/")))
        for pattern in patterns
    )


def _filter_input_problems(workflow: dict[str, Any], alef: dict[str, Any]) -> list[str]:
    filters = yaml.safe_load(_filter_step(workflow)["with"]["filters"])
    outputs = workflow["jobs"]["changes"]["outputs"]
    packages = _cargo_packages()
    problems = []
    for job_id, job in workflow["jobs"].items():
        output = outputs.get(f"run-{job_id}")
        if output is None:
            continue
        patterns = {pattern for name in OUTPUT_FILTER.findall(output) for pattern in filters[name]}
        problems.extend(
            f"{job_id}: no assigned filter covers {path}"
            for path in sorted(_job_inputs(job, alef, packages))
            if not _covered(path, patterns)
        )
    return problems


def test_every_e2e_leg_filter_covers_the_inputs_its_job_reads() -> None:
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    alef = tomllib.loads(ALEF_PATH.read_text(encoding="utf-8"))

    assert _filter_input_problems(workflow, alef) == []


def test_missing_jni_filter_input_is_reported() -> None:
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    alef = tomllib.loads(ALEF_PATH.read_text(encoding="utf-8"))
    changed = copy.deepcopy(workflow)
    filters = yaml.safe_load(_filter_step(changed)["with"]["filters"])
    filters["kotlin"].remove("crates/html-to-markdown-rs-jni/**")
    _filter_step(changed)["with"]["filters"] = yaml.safe_dump(filters)

    problems = _filter_input_problems(changed, alef)

    assert "build-kotlin-android: no assigned filter covers crates/html-to-markdown-rs-jni" in problems
