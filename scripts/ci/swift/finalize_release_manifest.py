"""Write the Swift artifact checksum while preserving release provenance."""

import argparse
import re
import subprocess
from pathlib import Path

PLACEHOLDER = "__ALEF_SWIFT_CHECKSUM__"
CHECKSUM_PATTERN = re.compile(rf'checksum: "({PLACEHOLDER}|[0-9a-f]{{64}})"')


def git(repository: Path, *arguments: str) -> str:
    """Run Git in the release checkout and return stdout."""
    return subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def verify_previous_checksum_commit(repository: Path, manifest: Path, old_checksum: str) -> None:
    """Require the current commit to be one exact prior checksum substitution."""
    head = git(repository, "rev-parse", "HEAD").strip()
    headers = git(repository, "cat-file", "-p", head).partition("\n\n")[0].splitlines()
    parents = [line.removeprefix("parent ") for line in headers if line.startswith("parent ")]
    if len(parents) != 1:
        raise ValueError("Existing Swift checksum commit must have exactly one parent")
    parent = parents[0]
    relative_manifest = manifest.relative_to(repository).as_posix()
    if git(repository, "diff", "--name-only", parent, head).splitlines() != [relative_manifest]:
        raise ValueError("Existing Swift checksum commit changes files beyond Package.swift")
    if (
        git(repository, "ls-tree", parent, "--", relative_manifest).split()[:2]
        != git(repository, "ls-tree", head, "--", relative_manifest).split()[:2]
    ):
        raise ValueError("Existing Swift checksum commit changes the manifest file mode or type")
    original = git(repository, "show", f"{parent}:{relative_manifest}")
    current = git(repository, "show", f"{head}:{relative_manifest}")
    if original.count(PLACEHOLDER) != 1 or current != original.replace(PLACEHOLDER, old_checksum):
        raise ValueError("Existing Swift checksum commit is not an exact placeholder substitution")


def finalize(repository: Path, manifest: Path, checksum: str, version: str) -> None:
    """Create, amend, or preserve the single allowed checksum-only commit."""
    if re.fullmatch(r"[0-9a-f]{64}", checksum) is None:
        raise ValueError("Expected a single lowercase SHA256 checksum")
    source = manifest.read_text(encoding="utf-8")
    matches = CHECKSUM_PATTERN.findall(source)
    if len(matches) != 1:
        raise ValueError("Package.swift must contain exactly one placeholder or SHA256 checksum")
    old_value = matches[0]
    if old_value == checksum:
        return
    if old_value != PLACEHOLDER:
        verify_previous_checksum_commit(repository, manifest, old_value)
    manifest.write_text(CHECKSUM_PATTERN.sub(f'checksum: "{checksum}"', source), encoding="utf-8")
    git(repository, "add", str(manifest.relative_to(repository)))
    if old_value == PLACEHOLDER:
        git(repository, "commit", "-m", f"chore(release): update Swift checksum for {version}")
    else:
        git(repository, "commit", "--amend", "--no-edit")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checksum")
    parser.add_argument("version")
    parser.add_argument("manifest", type=Path, nargs="?", default=Path("Package.swift"))
    arguments = parser.parse_args()
    root = Path.cwd().resolve()
    finalize(root, arguments.manifest.resolve(), arguments.checksum, arguments.version)
