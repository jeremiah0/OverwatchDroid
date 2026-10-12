#!/usr/bin/env bash
# Compare repo SHA256SUMS against what is on the Thor right now.
set -euo pipefail
source "$(dirname "$0")/env.sh"
cd "$REPO"

device=$(adbsu "cd $COMPONENTS/store && sha256sum $(awk '{print $2}' SHA256SUMS | tr '\n' ' ')" | tr -d '\r')
if diff <(sed 's#  \./#  #' SHA256SUMS) <(echo "$device" | sed 's#  \./#  #') ; then
  echo "store: device matches repo"
else
  echo "store: DIFFERS (< repo, > device)"; exit 1
fi

# The wiring that actually puts the patched ntdll into Proton for Overwatch.
adbsu "grep \"^$APPID\" $COMPONENTS/desired.tsv | grep ntdll" | tr -d '\r'
