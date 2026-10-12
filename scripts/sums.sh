#!/usr/bin/env bash
# Regenerate SHA256SUMS for everything under store/.
set -euo pipefail
cd "$(dirname "$0")/../store"
find . -type f ! -name .complete | sort | xargs shasum -a 256 > ../SHA256SUMS
