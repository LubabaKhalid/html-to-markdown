"""Keep every gated E2E job's path filters aligned with the inputs it reads."""

import copy
import posixpath
import re
import tomllib
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "ci-e2e.yaml"
DELEGATED_WORKFLOW_PATH = ROOT / ".github" / "workflows" / "ci-e2e-delegated.yaml"
ALEF_PATH = ROOT / "alef.toml"
OUTPUT_FILTER = re.compile(r"steps\.filter\.outputs\.([a-z]+) == 'true'")
ALEF_LANGUAGE = re.compile(r"alef test --e2e --lang ([a-z_]+)")
CARGO_PACKAGE = re.compile(r"(?:^|\s)-p\s+([a-z0-9_-]+)")
SCRIPT_PATH = re.compile(r"(?:^|[\s\"'])((?:\.\.?/)*scripts/[A-Za-z0-9_./-]+)")
CHANGE_DIRECTORY = re.compile(r"(?:^|&&|;)\s*cd\s+([^\s;&]+)")
REPOSITORY_PATH_PREFIXES = ("crates/", "packages/", "e2e/", "scripts/")


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


def _repository_path(path: object, working_directory: str = ".") -> str | None:
    value = str(path).strip("'\"")
    if not value or "${{" in value or value.startswith("/"):
        return None
    resolved = posixpath.normpath(posixpath.join(working_directory, value))
    if resolved.startswith(REPOSITORY_PATH_PREFIXES):
        return resolved
    return None


def _command_inputs(command: str, working_directory: str, packages: dict[str, str]) -> set[str]:
    inputs = {
        path
        for match in SCRIPT_PATH.findall(command)
        if (path := _repository_path(match, working_directory)) is not None
    }
    inputs.update(
        path
        for match in CHANGE_DIRECTORY.findall(command)
        if (path := _repository_path(match, working_directory)) is not None
    )
    inputs.update(packages[package] for package in CARGO_PACKAGE.findall(command))
    return inputs


def _job_inputs(
    job: dict[str, Any], alef: dict[str, Any], packages: dict[str, str], workflow_inputs: set[str]
) -> set[str]:
    inputs = set(workflow_inputs)
    commands = _commands(job, alef)
    if any(ALEF_LANGUAGE.search(command) for command in commands):
        inputs.add("alef.toml")
    for step in job.get("steps", []):
        working_directory = str(step.get("working-directory", "."))
        if directory := _repository_path(working_directory):
            inputs.add(directory)
        options = step.get("with", {})
        for key, value in options.items():
            if (key == "working-directory" or key.endswith(("-dir", "-script"))) and (path := _repository_path(value)):
                inputs.add(path)
        for key in ("crate-name", "ffi-crate-name"):
            if package := options.get(key):
                inputs.add(packages[str(package)])
        inputs.update(_command_inputs(str(step.get("run", "")), working_directory, packages))
    step_commands = {str(step.get("run", "")) for step in job.get("steps", [])}
    for command in commands:
        if command not in step_commands:
            inputs.update(_command_inputs(command, ".", packages))
    return inputs


def _covered(path: str, patterns: set[str]) -> bool:
    return any(
        pattern == path or (pattern.endswith("/**") and (path == pattern[:-3] or path.startswith(f"{pattern[:-3]}/")))
        for pattern in patterns
    )


def _resolved_job(job: dict[str, Any], delegated: dict[str, Any]) -> tuple[dict[str, Any], set[str]]:
    workflow_inputs = {".github/workflows/ci-e2e.yaml"}
    if job.get("uses") != "./.github/workflows/ci-e2e-delegated.yaml":
        return job, workflow_inputs

    workflow_inputs.add(".github/workflows/ci-e2e-delegated.yaml")
    task = str(job.get("with", {}).get("task", ""))
    return delegated["jobs"][task], workflow_inputs


def _filter_input_problems(workflow: dict[str, Any], delegated: dict[str, Any], alef: dict[str, Any]) -> list[str]:
    filters = yaml.safe_load(_filter_step(workflow)["with"]["filters"])
    outputs = workflow["jobs"]["changes"]["outputs"]
    packages = _cargo_packages()
    problems = []
    for job_id, job in workflow["jobs"].items():
        output = outputs.get(f"run-{job_id}")
        if output is None:
            continue
        resolved_job, workflow_inputs = _resolved_job(job, delegated)
        patterns = {pattern for name in OUTPUT_FILTER.findall(output) for pattern in filters[name]}
        problems.extend(
            f"{job_id}: no assigned filter covers {path}"
            for path in sorted(_job_inputs(resolved_job, alef, packages, workflow_inputs))
            if not _covered(path, patterns)
        )
    return problems


def test_every_e2e_leg_filter_covers_the_inputs_its_job_reads() -> None:
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    delegated = yaml.safe_load(DELEGATED_WORKFLOW_PATH.read_text(encoding="utf-8"))
    alef = tomllib.loads(ALEF_PATH.read_text(encoding="utf-8"))

    assert _filter_input_problems(workflow, delegated, alef) == []


def test_missing_jni_filter_input_is_reported() -> None:
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    delegated = yaml.safe_load(DELEGATED_WORKFLOW_PATH.read_text(encoding="utf-8"))
    alef = tomllib.loads(ALEF_PATH.read_text(encoding="utf-8"))
    changed = copy.deepcopy(workflow)
    filters = yaml.safe_load(_filter_step(changed)["with"]["filters"])
    filters["kotlin"].remove("crates/html-to-markdown-rs-jni/**")
    _filter_step(changed)["with"]["filters"] = yaml.safe_dump(filters)

    problems = _filter_input_problems(changed, delegated, alef)

    assert "build-kotlin-android: no assigned filter covers crates/html-to-markdown-rs-jni" in problems


def test_missing_action_script_filter_input_is_reported() -> None:
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    alef = tomllib.loads(ALEF_PATH.read_text(encoding="utf-8"))
    changed = copy.deepcopy(workflow)
    filters = yaml.safe_load(_filter_step(changed)["with"]["filters"])
    filters["r"].remove("scripts/ci/r/**")
    _filter_step(changed)["with"]["filters"] = yaml.safe_dump(filters)

    problems = _filter_input_problems(changed, alef)

    assert "test-r: no assigned filter covers scripts/ci/r/install-deps.sh" in problems


def test_missing_action_working_directory_filter_input_is_reported() -> None:
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    alef = tomllib.loads(ALEF_PATH.read_text(encoding="utf-8"))
    changed = copy.deepcopy(workflow)
    filters = yaml.safe_load(_filter_step(changed)["with"]["filters"])
    filters["ruby"].remove("packages/ruby/**")
    _filter_step(changed)["with"]["filters"] = yaml.safe_dump(filters)

    problems = _filter_input_problems(changed, alef)

    assert "build-ruby: no assigned filter covers packages/ruby" in problems


def test_missing_relative_script_filter_input_is_reported() -> None:
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    alef = tomllib.loads(ALEF_PATH.read_text(encoding="utf-8"))
    changed = copy.deepcopy(workflow)
    filters = yaml.safe_load(_filter_step(changed)["with"]["filters"])
    filters["ruby"].remove("scripts/ci/ruby/**")
    _filter_step(changed)["with"]["filters"] = yaml.safe_dump(filters)

    problems = _filter_input_problems(changed, alef)

    assert "test-ruby: no assigned filter covers scripts/ci/ruby/run-rspec-unix.sh" in problems
