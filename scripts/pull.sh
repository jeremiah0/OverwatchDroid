#!/usr/bin/env bash
# Maintainer: refresh the repo from a device (store components, desired.tsv, game-environment.json).
set -euo pipefail
source "$(dirname "$0")/env.sh"
cd "$REPO"

mkdir -p store config
adb -s "$SERIAL" exec-out "su -c 'tar -C $COMPONENTS/store -cf - ${STORE_DIRS[*]}'" | tar -C store -xf -
# Only Overwatch's rows/entry are published; the full files stay local (gitignored) for reference.
adbcat "$COMPONENTS/desired.tsv" > config/desired.tsv
adbcat "$GAME_ENV" | python3 -I -c 'import json,sys; d=json.load(sys.stdin); json.dump({"version":1,"games":{"'$APPID'":d["games"]["'$APPID'"]}}, sys.stdout, separators=(",",":"))' > config/game-environment.json
new=$(grep "^$APPID	" config/desired.tsv | awk -F'\t' '$4=="ntdll" || $4=="fex"' || true)
# DroidDeck sometimes drops the ntdll rows; keep the published ones rather than losing them.
if grep -q '	ntdll	' <<<"$new"; then grep "^$APPID	" config/desired.tsv > config/desired-$APPID.tsv; else echo "device has no Overwatch ntdll row; kept config/desired-$APPID.tsv"; fi
chmod -R u+rwX store

"$REPO/scripts/sums.sh"
git status --short
