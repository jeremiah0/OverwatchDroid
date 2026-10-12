#!/usr/bin/env bash
# Patch Overwatch 2 on a DroidDeck install: pr47 ntdll.dll + d2rfix28 FEX + Low/DX12 settings.
#   install.sh             install
#   install.sh --dry-run   run all checks and show what would change, touch nothing
#   install.sh --uninstall put Valve's stock ntdll.dll back (FEX and game settings are kept)
# Needs: adb, python3, a rooted device (Magisk su), and Proton Experimental (ARM64)
# build experimental-11.0-20261008-arm64 installed in DroidDeck's Steam.
# Everything it replaces is saved to /data/local/tmp/ow-backup-<timestamp>/ on the device first.
set -euo pipefail
source "$(dirname "$0")/env.sh"
cd "$REPO"

mode=${1:-install}
case $mode in install|--dry-run|--uninstall) ;; *) die "unknown option '$mode'" ;; esac
stamp=$(date +%Y%m%d-%H%M%S)
stage=/data/local/tmp/ow-stage-$stamp
bak=/data/local/tmp/ow-backup-$stamp
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT

echo "device: $SERIAL, DroidDeck: $APP"
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

mkdir -p "$work/stage/store"
adbcat "$COMPONENTS/desired.tsv" > "$work/desired.device.tsv"
adbcat "$GAME_ENV" > "$work/env.device.json"

# Overwatch's Wine user folder: in DroidDeck's own Steam, or a Steam library on shared/SD storage.
# It only exists once Overwatch has been launched.
ow_user_rel=steamapps/compatdata/$APPID/pfx/drive_c/users/steamuser
ow_user=$(adbsu "for d in $LINUXFS/.local/share/Steam /storage/*/Android/data/$APP/files/steam; do [ -d \$d/$ow_user_rel ] && echo \$d/$ow_user_rel && break; done; true" | tr -d '\r' | head -1)
ow_settings=${ow_user:+$ow_user/Documents/Overwatch/Settings/Settings_v0.ini}

if [[ $mode == --uninstall ]]; then
  python3 -I scripts/owconfig.py stock-ntdll "$work/desired.device.tsv" "$work/stage/desired.tsv" \
    "$NTDLL_STOCK" "/root/.local/share/droiddeck-components/store/${STORE_DIRS[1]}/$NTDLL_REL"
  cp "$work/env.device.json" "$work/stage/game-environment.json"
  dirs=("${STORE_DIRS[1]}")
  want=$NTDLL_STOCK
else
  python3 -I scripts/owconfig.py merge "$work/desired.device.tsv" "config/desired-$APPID.tsv" \
    "$work/env.device.json" config/game-environment.json "$work/stage" "${STORE_DIRS[*]}"
  dirs=("${STORE_DIRS[@]}")
  want=$NTDLL_PR47
  if [[ -n "$ow_settings" ]]; then
    adbcat "$ow_settings" > "$work/settings.device.ini"
    python3 -I scripts/owconfig.py settings "$work/settings.device.ini" config/Settings_v0.ini "$work/stage/Settings_v0.ini"
  else
    echo "Settings_v0.ini: skipped, Overwatch hasn't been launched yet. Launch it once, quit, and rerun this to set Low + DX12."
  fi
fi
tar -C store -cf - "${dirs[@]}" | tar -C "$work/stage/store" -xf -

# DroidDeck may drop our desired.tsv rows (and the store dirs they point at) when it rewrites its
# component list, so the ntdll.dll also goes straight into Proton. DroidDeck leaves that file alone.
proton_new=$([[ $want == "$NTDLL_PR47" ]] && echo "${STORE_DIRS[0]}" || echo "${STORE_DIRS[1]}")
cp "store/$proton_new/$NTDLL_REL" "$work/stage/proton-ntdll.dll"
[[ $(shasum -a 256 "$work/stage/proton-ntdll.dll" | awk '{print $1}') == "$want" ]] || die "repo ntdll.dll hash mismatch"

if [[ $mode == --dry-run ]]; then
  echo; echo "--- Proton ntdll.dll: $ntdll -> $want"
  echo; echo "--- desired.tsv changes (Overwatch rows)"
  diff <(grep "^$APPID	" "$work/desired.device.tsv" | sort) <(grep "^$APPID	" "$work/stage/desired.tsv" | sort) || true
  echo; echo "--- game-environment.json Overwatch entry"
  python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["games"]["2357570"])' "$work/stage/game-environment.json"
  if [[ -f "$work/stage/Settings_v0.ini" ]]; then
    echo; echo "--- $ow_settings"
    diff <(tr -d '\r' < "$work/settings.device.ini") <(tr -d '\r' < "$work/stage/Settings_v0.ini") || true
  fi
  echo; echo "dry run: nothing changed on the device"
  exit 0
fi

cat > "$work/stage/apply.sh" <<APPLY
set -e
C="$COMPONENTS"; E="$GAME_ENV"; S="$stage"; B="$bak"; P="$PROTON_DIR/$NTDLL_REL"
ref="\$C"; [ -d "\$ref" ] || ref="\$(dirname "\$C")"
owner=\$(stat -c %u:%g "\$ref")
label=\$(ls -Zd "\$ref" | awk '{print \$1}')
fix() { chown -R \$owner "\$@"; chcon -R \$label "\$@"; chmod -R go-rwx "\$@"; }

mkdir -p "\$B"
for d in "\$C" "\$C/store" "\$(dirname "\$E")"; do [ -d "\$d" ] || { mkdir -p "\$d"; fix "\$d"; }; done
[ -f "\$C/desired.tsv" ] && cp -p "\$C/desired.tsv" "\$B/"
[ -f "\$E" ] && cp -p "\$E" "\$B/"
for d in ${dirs[*]}; do
  [ -d "\$C/store/\$d" ] && cp -a "\$C/store/\$d" "\$B/"
  rm -rf "\$C/store/\$d"
  cp -r "\$S/store/\$d" "\$C/store/"
  fix "\$C/store/\$d"
done
cat "\$S/desired.tsv" > "\$C/desired.tsv"
cat "\$S/game-environment.json" > "\$E"
fix "\$C/desired.tsv" "\$E"

# Overwriting in place keeps the file's owner, mode and SELinux label.
cp -p "\$P" "\$B/proton-ntdll.dll"
cat "\$S/proton-ntdll.dll" > "\$P"

W="$ow_settings"; U="$ow_user"
if [ -n "\$W" ] && [ -f "\$S/Settings_v0.ini" ]; then
  wo=\$(stat -c %u:%g "\$U"); wl=\$(ls -Zd "\$U" | awk '{print \$1}')
  wfix() { chown \$wo "\$1"; chcon \$wl "\$1" 2>/dev/null || true; }
  [ -f "\$W" ] && cp -p "\$W" "\$B/"
  for d in "\$U/Documents" "\$U/Documents/Overwatch" "\$(dirname "\$W")"; do
    [ -d "\$d" ] || { mkdir "\$d"; wfix "\$d"; chmod 700 "\$d"; }
  done
  cat "\$S/Settings_v0.ini" > "\$W"
  wfix "\$W"; chmod 600 "\$W"
fi
rm -rf "\$S"
APPLY

adb -s "$SERIAL" shell "mkdir -p $stage"
tar -C "$work/stage" -cf - . | adb -s "$SERIAL" shell "tar -C $stage -xf -"
adbsu "sh $stage/apply.sh"

echo "done. Previous files saved on the device in $bak"
"$REPO/scripts/verify.sh"
if [[ $mode == --uninstall ]]; then
  echo "Overwatch will use stock ntdll.dll on next launch."
else
  echo "Close other apps, then launch Overwatch with $PROTON_NAME."
fi
