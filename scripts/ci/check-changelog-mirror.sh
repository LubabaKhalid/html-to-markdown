#!/usr/bin/env bash
# Verify the docs-site changelog mirror carries the same entries as CHANGELOG.md.
set -euo pipefail

ROOT="CHANGELOG.md"
MIRROR="docs-site/src/content/docs/changelog.md"
ARCHIVE_COUNT=5

# ~keep Nothing syncs these two files, so they diverged unnoticed: the mirror's 3.15.0 section
# carried the wrong release date, was missing the alef re-pin and the R-binding entries, and
# summarised the Swift fix inaccurately. Everything from the first `## [` heading is compared,
# not just `## [Unreleased]` as the sibling check in crawlberg does: this repo releases straight
# out of `[Unreleased]`, leaving it empty on `main`, so an Unreleased-only comparison would
# compare zero lines and pass while a released section drifted. The mirror's frontmatter and
# preamble differ by design and sit above that heading, so they are excluded.
# ~keep Trailing blank lines are formatter-owned and carry no entry content, so only those are
# ~keep discarded; blank lines between entries remain part of the byte-for-byte comparison.
extract_entries() {
  awk '
    /^## \[/ { found = 1 }
    found && /^[[:space:]]*$/ { pending += 1; next }
    found {
      while (pending > 0) {
        print ""
        pending -= 1
      }
      print
    }
  ' "$1"
}

workdir="$(mktemp -d)"
[ -n "$workdir" ] && [ -d "$workdir" ] || exit 90
trap 'rm -rf "$workdir"' EXIT

failures=0
check_file() {
  path="$1"
  if [ ! -f "$path" ]; then
    echo "::error::$path is missing"
    failures=$((failures + 1))
  elif ! grep -q '^## \[' "$path"; then
    echo "::error::$path has no '## [' version heading — this check would compare nothing"
    failures=$((failures + 1))
  fi
}

compare_pair() {
  root="$1"
  mirror="$2"
  label="$3"
  check_file "$root"
  check_file "$mirror"
  [ "$failures" -eq 0 ] || return

  extract_entries "$root" >"$workdir/root-$label.txt"
  extract_entries "$mirror" >"$workdir/mirror-$label.txt"
  root_lines="$(wc -l <"$workdir/root-$label.txt" | tr -d ' ')"
  mirror_lines="$(wc -l <"$workdir/mirror-$label.txt" | tr -d ' ')"
  echo "changelog entries: $root has $root_lines lines, $mirror has $mirror_lines lines"

  if [ "$root_lines" -eq 0 ]; then
    echo "::error::no changelog entries were extracted from $root — nothing was compared"
    failures=$((failures + 1))
    return
  fi

  if ! diff -q "$workdir/root-$label.txt" "$workdir/mirror-$label.txt" >/dev/null 2>&1; then
    diff -u "$workdir/root-$label.txt" "$workdir/mirror-$label.txt" | head -60
    echo "::error::$mirror is a hand-maintained mirror of $root and has drifted. Copy the changed entries from $root into $mirror."
    failures=$((failures + 1))
    return
  fi

  echo "ok: the changelog entries match ($root_lines lines)"
}

compare_pair "$ROOT" "$MIRROR" main
archive=1
while [ "$archive" -le "$ARCHIVE_COUNT" ]; do
  compare_pair "changelog-archive-$archive.md" "docs-site/src/content/docs/changelog-archive-$archive.md" "archive-$archive"
  archive=$((archive + 1))
done

[ "$failures" -eq 0 ] || exit 1
