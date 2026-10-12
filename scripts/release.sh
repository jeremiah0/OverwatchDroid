#!/usr/bin/env bash
# Build a release archive from a clean, committed tree and tag it.
#   release.sh v1.0.0 "short description"
# Output: dist/overwatch-droid-<version>.tar.gz and .zip, plus .sha256 files.
# backups/ is left out via export-ignore in .gitattributes (same as GitHub's tag downloads).
set -euo pipefail
cd "$(dirname "$0")/.."

version=${1:?usage: release.sh VERSION [MESSAGE]}
message=${2:-"Overwatch Droid $version"}
name=overwatch-droid-$version

[[ -z "$(git status --porcelain)" ]] || { echo "working tree not clean"; exit 1; }
git rev-parse -q --verify "refs/tags/$version" >/dev/null && { echo "tag $version exists"; exit 1; }

(cd store && shasum -a 256 -c ../SHA256SUMS --quiet) || { echo "store/ doesn't match SHA256SUMS"; exit 1; }

git tag -a "$version" -m "$message"

mkdir -p dist
git archive --format=tar.gz --prefix="$name/" -o "dist/$name.tar.gz" "$version"
git archive --format=zip    --prefix="$name/" -o "dist/$name.zip"    "$version"
(cd dist && for f in "$name.tar.gz" "$name.zip"; do shasum -a 256 "$f" > "$f.sha256"; done)

ls -la dist/$name.*
cat dist/$name.*.sha256
