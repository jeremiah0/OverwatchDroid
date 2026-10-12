#!/usr/bin/env bash
# Patch Overwatch 2 on a DroidDeck install: pr47 ntdll.dll + d2rfix28 FEX + low graphics settings.
#   install.sh              check everything, show what will change, ask, then install
#   install.sh --dry-run    check everything and show the exact changes; touch nothing
#   install.sh --uninstall  put Valve's stock ntdll.dll back (FEX and game settings are kept)
#   add --yes to skip the questions
# Needs: adb, python3, a rooted device (Magisk su), and Proton Experimental (ARM64)
# build experimental-11.0-20261008-arm64 installed in DroidDeck's Steam.
# Everything it replaces is saved to /data/local/tmp/ow-backup-<timestamp>/ on the device first.
set -euo pipefail

mode=install
ASSUME_YES=0
for arg in "$@"; do
  case $arg in
    --dry-run|--uninstall) mode=$arg ;;
    -y|--yes) ASSUME_YES=1 ;;
    -h|--help) sed -n '2,9s/^# \{0,1\}//p' "$0"; exit 0 ;;
    *) echo "error: unknown option '$arg' (try --help)" >&2; exit 1 ;;
  esac
done
command -v python3 >/dev/null || { echo "error: python3 not found. Mac: run 'xcode-select --install'. Linux: install python3 with your package manager." >&2; exit 1; }

source "$(dirname "$0")/env.sh"
cd "$REPO"

stamp=$(date +%Y%m%d-%H%M%S)
stage=$DEVICE_TMP/ow-stage-$stamp
bak=$DEVICE_TMP/ow-backup-$stamp
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT

echo "device: $SERIAL, DroidDeck: $APP"
adbsu "test -d $LINUXFS" || die "DroidDeck Linux root not found at $LINUXFS"
# DroidDeck rewrites its config while it runs, so it has to be closed before anything is read or written.
if [[ $mode != --dry-run ]] && adb -s "$SERIAL" shell pidof "$APP" >/dev/null; then
  confirm "DroidDeck is running and has to be closed first. Close it now?" ||
    die "close DroidDeck (swipe it away or force stop it), then rerun."
  adb -s "$SERIAL" shell am force-stop "$APP"
  for _ in 1 2 3 4 5; do adb -s "$SERIAL" shell pidof "$APP" >/dev/null || break; sleep 1; done
  ! adb -s "$SERIAL" shell pidof "$APP" >/dev/null || die "DroidDeck is still running. Force stop it in Android's app settings, then rerun."
fi

version=$(adbcat "$PROTON_DIR/version" | awk '{print $2}')
[[ "$version" == "$PROTON_VERSION" ]] ||
  die "need $PROTON_NAME build $PROTON_VERSION, found '${version:-not installed}'. The ntdll patch only fits that exact build.
See \"When Proton updates\" in the README."
ntdll=$(adbsu "sha256sum \"$PROTON_DIR/$NTDLL_REL\"" | awk '{print $1}')
case $ntdll in
  "$NTDLL_STOCK") echo "Proton ntdll.dll: stock" ;;
  "$NTDLL_PR47")  echo "Proton ntdll.dll: already pr47" ;;
  *) die "Proton's ntdll.dll is an unknown version ($ntdll), so it won't be replaced. Ask Steam to verify $PROTON_NAME's files and rerun." ;;
esac

mkdir -p "$work/stage/store"
adbcat "$COMPONENTS/desired.tsv" > "$work/desired.device.tsv"
adbcat "$GAME_ENV" > "$work/env.device.json"
adbcat "$APP_ENV" > "$work/env.app.json"

# Overwatch's Wine user folder: in DroidDeck's own Steam, or a Steam library on shared/SD storage.
# It only exists once Overwatch has been launched.
ow_user_rel=steamapps/compatdata/$APPID/pfx/drive_c/users/steamuser
ow_user=$(adbsu "for d in $LINUXFS/.local/share/Steam /storage/*/Android/data/$APP/files/steam; do [ -d \$d/$ow_user_rel ] && echo \$d/$ow_user_rel && break; done; true" | tr -d '\r' | head -1)
ow_settings=${ow_user:+$ow_user/Documents/Overwatch/Settings/Settings_v0.ini}

if [[ $mode == --uninstall ]]; then
  if [[ $ntdll == "$NTDLL_STOCK" ]] && ! awk -F'\t' -v a="$APPID" -v h="$NTDLL_STOCK" '$1==a && $4=="ntdll" && $6!=h {f=1} END {exit !f}' "$work/desired.device.tsv"; then
    echo "nothing to uninstall: Overwatch already uses the stock ntdll.dll"; exit 0
  fi
  python3 -I scripts/owconfig.py stock-ntdll "$work/desired.device.tsv" "$work/stage/desired.tsv" \
    "$NTDLL_STOCK" "/root/.local/share/droiddeck-components/store/${STORE_DIRS[1]}/$NTDLL_REL"
  cp "$work/env.device.json" "$work/stage/game-environment.json"
  dirs=("${STORE_DIRS[1]}")
  want=$NTDLL_STOCK
else
  python3 -I scripts/owconfig.py merge "$work/desired.device.tsv" "config/desired-$APPID.tsv" \
    "$work/env.device.json" config/game-environment.json "$work/stage" "${STORE_DIRS[*]}"
  python3 -I scripts/owconfig.py env "$work/env.app.json" config/game-environment.json "$work/stage/game-environment.app.json"
  dirs=("${STORE_DIRS[@]}")
  want=$NTDLL_PR47
  if [[ -n "$ow_settings" ]]; then
    adbcat "$ow_settings" > "$work/settings.device.ini"
    python3 -I scripts/owconfig.py settings "$work/settings.device.ini" config/Settings_v0.ini "$work/stage/Settings_v0.ini"
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
  python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["games"][sys.argv[2]])' "$work/stage/game-environment.json" "$APPID"
  if [[ -f "$work/stage/Settings_v0.ini" ]]; then
    echo; echo "--- $ow_settings"
    diff <(tr -d '\r' < "$work/settings.device.ini") <(tr -d '\r' < "$work/stage/Settings_v0.ini") || true
  else
    echo; echo "--- Settings_v0.ini: not found, Overwatch hasn't been launched yet"
  fi
  echo; echo "dry run: nothing changed on the device"
  exit 0
fi

describe() { case $1 in "$NTDLL_PR47") echo pr47 ;; "$NTDLL_STOCK") echo stock ;; esac; }
echo
if [[ $mode == --uninstall ]]; then
  echo "Ready to put back Valve's stock ntdll.dll (currently $(describe "$ntdll")). FEX and game settings stay as they are."
  question="Uninstall?"
else
  echo "Ready to patch Overwatch on $SERIAL (DroidDeck: $APP):"
  echo "  ntdll.dll  $(describe "$ntdll") -> pr47"
  echo "  FEX        d2rfix28, with Overwatch's FEX settings"
  if [[ -n "$ow_settings" ]]; then
    echo "  Graphics   Low preset, DirectX 12, 50% render scale, 30 fps cap"
  else
    echo "  Graphics   skipped: launch Overwatch once, quit from its menu, then run this again"
  fi
  echo "Other games aren't touched."
  question="Install?"
fi
echo "Files that get replaced are backed up on the device to $bak"
confirm "$question" || { echo "cancelled; nothing changed"; exit 0; }
echo

cat > "$work/stage/apply.sh" <<APPLY
set -e
C="$COMPONENTS"; E="$GAME_ENV"; A="$APP_ENV"; S="$stage"; B="$bak"; P="$PROTON_DIR/$NTDLL_REL"
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

# DroidDeck's master copy of the per-game environment; it overwrites \$E at session start.
if [ -f "\$S/game-environment.app.json" ]; then
  [ -f "\$A" ] && cp -p "\$A" "\$B/game-environment.app.json"
  ao=\$(stat -c %u:%g "\$(dirname "\$A")"); al=\$(ls -Zd "\$(dirname "\$A")" | awk '{print \$1}')
  cat "\$S/game-environment.app.json" > "\$A"
  chown \$ao "\$A"; chcon \$al "\$A" 2>/dev/null || true; chmod 600 "\$A"
fi

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

echo
ANDROID_SERIAL=$SERIAL DROIDDECK_PACKAGE=$APP "$REPO/scripts/verify.sh"
echo
echo "Done. Previous files are saved on the device in $bak"
if [[ $mode == --uninstall ]]; then
  echo "Overwatch will use the stock ntdll.dll on its next launch."
else
  echo "Next: close other apps, open DroidDeck and play Overwatch with $PROTON_NAME."
  echo "If Steam updates $PROTON_NAME, run this again."
fi
