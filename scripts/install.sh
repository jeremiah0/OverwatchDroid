#!/usr/bin/env bash
# Patch Overwatch 2 on a DroidDeck install: pr47 ntdll.dll + d2rfix28 FEX.
#   install.sh             install
#   install.sh --dry-run   run all checks and show what would change, touch nothing
#   install.sh --uninstall point Overwatch back at Valve's stock ntdll.dll
# Needs: adb, python3, a rooted device (Magisk su), and Proton Experimental (ARM64)
# build experimental-11.0-20261008-arm64 installed in DroidDeck's Steam.
# Everything it replaces is saved to /data/local/tmp/ow-backup-<timestamp>/ on the device first.
set -euo pipefail
source "$(dirname "$0")/env.sh"
cd "$REPO"

mode=${1:-install}
stamp=$(date +%Y%m%d-%H%M%S)
stage=/data/local/tmp/ow-stage-$stamp
bak=/data/local/tmp/ow-backup-$stamp
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT

echo "device: $SERIAL"
adbsu id | grep -q 'uid=0' || die "no root. Allow root for Shell in Magisk and rerun."
adbsu "test -d $LINUXFS" || die "DroidDeck Linux root not found at $LINUXFS"
if [[ $mode != --dry-run ]] && adb -s "$SERIAL" shell pidof "$APP" >/dev/null; then
  die "DroidDeck is running. Close it (swipe away or force stop), then rerun."
fi

version=$(adbcat "$PROTON_DIR/version" | awk '{print $2}')
[[ "$version" == "$PROTON_VERSION" ]] ||
  die "need $PROTON_NAME $PROTON_VERSION, found '${version:-not installed}'. This ntdll patch only fits that exact build."
ntdll=$(adbsu "sha256sum \"$PROTON_DIR/$NTDLL_REL\"" | awk '{print $1}')
case $ntdll in
  "$NTDLL_STOCK") echo "Proton ntdll.dll: stock" ;;
  "$NTDLL_PR47")  echo "Proton ntdll.dll: already pr47" ;;
  *) die "Proton's ntdll.dll is an unknown version ($ntdll); refusing to replace it." ;;
esac

mkdir -p "$work/stage"
adbcat "$COMPONENTS/desired.tsv" > "$work/desired.device.tsv"
adbcat "$GAME_ENV" > "$work/env.device.json"

if [[ $mode == --uninstall ]]; then
  python3 -I scripts/owconfig.py stock-ntdll "$work/desired.device.tsv" "$work/stage/desired.tsv" \
    "$NTDLL_STOCK" "/root/.local/share/droiddeck-components/store/${STORE_DIRS[1]}/$NTDLL_REL"
  cp "$work/env.device.json" "$work/stage/game-environment.json"
  dirs=()
else
  python3 -I scripts/owconfig.py merge "$work/desired.device.tsv" "config/desired-$APPID.tsv" \
    "$work/env.device.json" config/game-environment.json "$work/stage" "${STORE_DIRS[*]}"
  mkdir -p "$work/stage/store"
  tar -C store -cf - "${STORE_DIRS[@]}" | tar -C "$work/stage/store" -xf -
  dirs=("${STORE_DIRS[@]}")
fi

if [[ $mode == --dry-run ]]; then
  echo; echo "--- desired.tsv changes (Overwatch rows)"
  diff <(grep "^$APPID	" "$work/desired.device.tsv" | sort) <(grep "^$APPID	" "$work/stage/desired.tsv" | sort) || true
  echo; echo "--- game-environment.json Overwatch entry"
  python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["games"]["2357570"])' "$work/stage/game-environment.json"
  echo; echo "dry run: nothing changed on the device"
  exit 0
fi

cat > "$work/stage/apply.sh" <<APPLY
set -e
C="$COMPONENTS"; E="$GAME_ENV"; S="$stage"; B="$bak"
ref="\$C"; [ -d "\$ref" ] || ref="\$(dirname "\$C")"
owner=\$(stat -c %u:%g "\$ref")
label=\$(ls -Zd "\$ref" | awk '{print \$1}')
fix() { chown -R \$owner "\$@"; chcon -R \$label "\$@"; chmod -R go-rwx "\$@"; }

mkdir -p "\$B"
for d in "\$C" "\$C/store" "\$(dirname "\$E")"; do [ -d "\$d" ] || { mkdir -p "\$d"; fix "\$d"; }; done
[ -f "\$C/desired.tsv" ] && cp -p "\$C/desired.tsv" "\$B/"
[ -f "\$E" ] && cp -p "\$E" "\$B/"
for d in ${dirs[*]:-}; do
  [ -d "\$C/store/\$d" ] && cp -a "\$C/store/\$d" "\$B/"
  rm -rf "\$C/store/\$d"
  cp -r "\$S/store/\$d" "\$C/store/"
  fix "\$C/store/\$d"
done
cat "\$S/desired.tsv" > "\$C/desired.tsv"
cat "\$S/game-environment.json" > "\$E"
fix "\$C/desired.tsv" "\$E"
rm -rf "\$S"
APPLY

adb -s "$SERIAL" shell "mkdir -p $stage"
tar -C "$work/stage" -cf - . | adb -s "$SERIAL" shell "tar -C $stage -xf -"
adbsu "sh $stage/apply.sh"

echo "done. Previous files saved on the device in $bak"
[[ $mode == --uninstall ]] && echo "Overwatch will use stock ntdll.dll on next launch." && exit 0
"$REPO/scripts/verify.sh"
echo "Launch Overwatch with $PROTON_NAME."
