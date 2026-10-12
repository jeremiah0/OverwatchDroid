#!/usr/bin/env bash
# Show what's actually in effect on the device for Overwatch. Read-only.
set -euo pipefail
source "$(dirname "$0")/env.sh"
cd "$REPO"

ntdll=$(adbsu "sha256sum \"$PROTON_DIR/$NTDLL_REL\" 2>/dev/null" | awk '{print $1}')
case $ntdll in
  "$NTDLL_PR47")  echo "Proton ntdll.dll: pr47 (patched)" ;;
  "$NTDLL_STOCK") echo "Proton ntdll.dll: stock" ;;
  *)              echo "Proton ntdll.dll: unknown (${ntdll:-missing})" ;;
esac

# DroidDeck deletes store dirs nothing points at any more, so missing ones aren't an error.
status=0
for d in "${STORE_DIRS[@]}"; do
  files=$(grep "  \./$d/" SHA256SUMS | awk '{print $2}' | tr '\n' ' ')
  device=$(adbsu "cd $COMPONENTS/store 2>/dev/null && [ -d $d ] && sha256sum $files" | tr -d '\r')
  if [[ -z "$device" ]]; then
    echo "store $d: not present"
  elif diff -q <(grep "  \./$d/" SHA256SUMS) <(echo "$device") >/dev/null; then
    echo "store $d: matches repo"
  else
    echo "store $d: DIFFERS from repo"; status=1
  fi
done

rows=$(adbcat "$COMPONENTS/desired.tsv" | awk -F'\t' -v a="$APPID" '$1==a && ($4=="ntdll" || $4=="fex")' | wc -l | tr -d ' ')
echo "desired.tsv: $rows Overwatch ntdll/fex rows"
exit $status
