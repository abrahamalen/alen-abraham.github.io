#!/usr/bin/env bash
# Regenerate site/urls.txt from a Hugo build. Only needed while Hugo is still around.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "${tmp}"' EXIT
hugo --minify -s "${root}" -d "${tmp}" >/dev/null
{
  echo "# Every file the Hugo build published (hugo --minify @ $(git -C "${root}" rev-parse --short HEAD)), frozen for URL parity."
  echo "# Excluded: /assets/* (Hugo's fingerprinted bundles) and /index.json (search index, dropped on purpose)."
  (cd "${tmp}" && find . -type f | sed 's|^\.||' | grep -v '^/assets/' | grep -v '^/index.json$' | sort)
} > "${root}/site/urls.txt"
