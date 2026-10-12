#!/usr/bin/env bash
# Maintainer: refresh the repo from a device (store components, desired.tsv, game-environment.json).
set -euo pipefail
source "$(dirname "$0")/env.sh"
cd "$REPO"

mkdir -p store config
adb -s "$SERIAL" exec-out "su -c 'tar -C $COMPONENTS/store -cf - ${STORE_DIRS[*]}'" | tar -C store -xf -
adbcat "$COMPONENTS/desired.tsv" > config/desired.tsv
adbcat "$COMPONENTS/reapplied.log" > config/reapplied.log
adbcat "$GAME_ENV" > config/game-environment.json
grep "^$APPID	" config/desired.tsv > config/desired-$APPID.tsv || true
chmod -R u+rwX store

"$REPO/scripts/sums.sh"
git status --short
