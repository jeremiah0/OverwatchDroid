# Shared settings. Overrides:
#   ANDROID_SERIAL     pick a device when more than one is connected
#   DROIDDECK_PACKAGE  skip auto-detection and use this app package
#   OW_LINUXFS         use this Linux root directly (testing)
#   OW_DATA_ROOT       where to look for app data dirs (default /data/user/0; testing)
APPID=2357570  # Overwatch 2

PROTON_NAME="Proton Experimental (ARM64)"
PROTON_VERSION=experimental-11.0-20261008-arm64
PROTON_SUBDIR=".local/share/Steam/steamapps/common/$PROTON_NAME"
NTDLL_REL=files/lib/wine/aarch64-windows/ntdll.dll
NTDLL_STOCK=541403217f19deed9cd984ebd59f2ec71e708421e135c9d254bbb908d86e4046
NTDLL_PR47=fb6022ab71709d6aa671e686b6d916e0aea30b77ce2be6279fd03e21e359392f

STORE_DIRS=(
  ntdll-pr47-experimental-11.0-20261008
  original-Proton_Experimental_ARM64-experimental-11.0-20261008-arm64-ntdll
  FEXCore-2610-d2rfix28-linux
)

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

die() { echo "error: $*" >&2; exit 1; }

if [[ -z "${ANDROID_SERIAL:-}" ]]; then
  _devices=$(adb devices | awk 'NR>1 && $2=="device" {print $1}')
  _count=$(grep -c . <<<"$_devices" || true)
  [[ $_count -eq 1 ]] || die "found $_count adb devices; set ANDROID_SERIAL to one of: $(echo $_devices)"
  SERIAL=$_devices
else
  SERIAL=$ANDROID_SERIAL
fi

adbsu() { adb -s "$SERIAL" shell "su -c '$*'"; }
# Print a device file as root (empty output if it doesn't exist).
adbcat() { adb -s "$SERIAL" exec-out "su -c 'cat \"$1\" 2>/dev/null'"; }

adbsu id 2>/dev/null | grep -q 'uid=0' || die "no root on $SERIAL. Allow root for Shell in Magisk and rerun."

# DroidDeck ships under different package names, so find it by its files rather than its name.
# If several installs are found, prefer the one(s) that have the required Proton build.
find_droiddeck() {
  local found with_proton
  found=$({ printf 'BASE=%q\nPROTON_SUBDIR=%q\n' "${OW_DATA_ROOT:-/data/user/0}" "$PROTON_SUBDIR"
            cat "$REPO/scripts/find-droiddeck.sh"; } | adb -s "$SERIAL" shell su -c sh | tr -d '\r')
  [[ -n "$found" ]] || die "DroidDeck not found on $SERIAL. Install it and open it once, or set DROIDDECK_PACKAGE."
  if [[ $(grep -c . <<<"$found") -gt 1 ]]; then
    with_proton=$(awk '$2==1' <<<"$found")
    [[ $(grep -c . <<<"$with_proton") -eq 1 ]] ||
      die "found several DroidDeck installs: $(awk '{print $1}' <<<"$found" | xargs). Set DROIDDECK_PACKAGE to one."
    found=$with_proton
  fi
  awk '{print $1}' <<<"$found"
}

if [[ -n "${OW_LINUXFS:-}" ]]; then
  APP="${DROIDDECK_PACKAGE:-test.droiddeck}"
  LINUXFS=$OW_LINUXFS
else
  if [[ -n "${DROIDDECK_PACKAGE:-}" ]]; then APP=$DROIDDECK_PACKAGE; else APP=$(find_droiddeck) || exit 1; fi
  LINUXFS="${OW_DATA_ROOT:-/data/user/0}/$APP/files/linuxfs/root"
fi
COMPONENTS=$LINUXFS/.local/share/droiddeck-components
GAME_ENV=$LINUXFS/.config/droiddeck/game-environment.json
PROTON_DIR="$LINUXFS/$PROTON_SUBDIR"
