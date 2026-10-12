#!/usr/bin/env bash
# Compare repo SHA256SUMS against the device's store, and show the active Overwatch ntdll row.
set -euo pipefail
source "$(dirname "$0")/env.sh"
cd "$REPO"

device=$(adbsu "cd $COMPONENTS/store && sha256sum $(awk '{print $2}' SHA256SUMS | tr '\n' ' ')" | tr -d '\r')
if diff SHA256SUMS <(echo "$device"); then
  echo "store: device matches repo"
else
  die "store: DIFFERS (< repo, > device)"
fi
adbcat "$COMPONENTS/desired.tsv" | grep "^$APPID	" | grep '	ntdll	' | cut -f1-4,6 || echo "no Overwatch ntdll row"
