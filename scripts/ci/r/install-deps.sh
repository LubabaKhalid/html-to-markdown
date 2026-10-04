#!/usr/bin/env bash
set -euo pipefail

if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends \
    libuv1-dev \
    libgit2-dev \
    libssl-dev \
    libcurl4-openssl-dev \
    libxml2-dev \
    libfontconfig1-dev \
    libfreetype6-dev \
    libharfbuzz-dev \
    libfribidi-dev
fi

if [[ "$(uname -s)" == "Linux" ]] && [[ -r /etc/os-release ]]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  REPO_URL="https://packagemanager.posit.co/cran/__linux__/${VERSION_CODENAME:-jammy}/latest"
  INSTALL_TYPE='"source"'
else
  REPO_URL="https://cran.r-project.org"
  INSTALL_TYPE='"binary"'
fi

Rscript -e "options(repos = c(CRAN = '${REPO_URL}')); for (pkg in c('devtools', 'testthat', 'rextendr', 'lintr', 'styler', 'covr', 'remotes')) { if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg, type = ${INSTALL_TYPE}) }"

# ~keep Roxygen output changes between releases. The committed pages declare 7.3.3, so the
# freshness gate must render with those exact bytes instead of whatever CRAN serves that day.
Rscript -e "options(repos = c(CRAN = '${REPO_URL}')); if (packageVersion('roxygen2') != '7.3.3') remotes::install_version('roxygen2', version = '7.3.3', upgrade = 'never')"
