#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../../.." && pwd)"
package_dir="${repo_root}/packages/r"
staging="$(mktemp -d)"
trap 'rm -rf "$staging"' EXIT

committed_count="$(find "${package_dir}/man" -maxdepth 1 -type f -name '*.Rd' | wc -l | tr -d ' ')"
if [ "${committed_count}" -eq 0 ]; then
  echo "No committed R reference pages found in packages/r/man." >&2
  exit 1
fi

mkdir -p "${staging}/package"
cp -R \
  "${package_dir}/DESCRIPTION" \
  "${package_dir}/NAMESPACE" \
  "${package_dir}/R" \
  "${staging}/package/"

roxygen_command='
if (as.character(utils::packageVersion("roxygen2")) != "7.3.3") {
  stop("roxygen2 7.3.3 is required")
}
roxygen2::roxygenise(commandArgs(trailingOnly = TRUE)[[1]], roclets = "rd", load_code = "source")
'
Rscript -e "${roxygen_command}" "${staging}/package"

rendered_count="$(find "${staging}/package/man" -maxdepth 1 -type f -name '*.Rd' | wc -l | tr -d ' ')"
if [ "${rendered_count}" -eq 0 ]; then
  echo "roxygen2 rendered zero R reference pages; refusing to report a false pass." >&2
  exit 1
fi

echo "R reference pages: committed=${committed_count} rendered=${rendered_count}"
if ! diff -ru "${package_dir}/man" "${staging}/package/man"; then
  echo "R reference pages are stale. Regenerate them with roxygen2 7.3.3 and commit packages/r/man/." >&2
  exit 1
fi

echo "R reference pages match a fresh roxygen2 render."
