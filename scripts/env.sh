# Shared settings and device checks. Overrides:
#   ANDROID_SERIAL     pick a device when more than one is connected
#   DROIDDECK_PACKAGE  skip auto-detection and use this app package
#   OW_LINUXFS         use this Linux root directly (testing)
#   OW_DATA_ROOT       where to look for app data dirs (default /data/user/0; testing)
#   OW_DEVICE_TMP      scratch dir on the device (default /data/local/tmp; testing)
APPID=2357570  # Overwatch 2

PROTON_NAME="Proton Experimental (ARM64)"
PROTON_VERSION=experimental-11.0-20261008-arm64
PROTON_SUBDIR=".local/share/Steam/steamapps/common/$PROTON_NAME"
NTDLL_REL=files/lib/wine/aarch64-windows/ntdll.dll
NTDLL_STOCK=541403217f19deed9cd984ebd59f2ec71e708421e135c9d254bbb908d86e4046
NTDLL_PR47=fb6022ab71709d6aa671e686b6d916e0aea30b77ce2be6279fd03e21e359392f
DEVICE_TMP=${OW_DEVICE_TMP:-/data/local/tmp}

STORE_DIRS=(
  ntdll-pr47-experimental-11.0-20261008
  original-Proton_Experimental_ARM64-experimental-11.0-20261008-arm64-ntdll
  FEXCore-2610-d2rfix28-linux
)

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

die() { echo "error: $*" >&2; exit 1; }
interactive() { [[ -t 0 && -t 2 ]]; }

# Ask a yes/no question (default yes). ASSUME_YES=1 answers yes without asking.
confirm() {
  [[ ${ASSUME_YES:-0} == 1 ]] && return 0
  interactive || die "not running in a terminal; rerun with --yes to skip the questions."
  local answer
  read -r -p "$1 [Y/n] " answer || { echo >&2; return 1; }
  [[ -z $answer || $answer == [yY]* ]]
}

# pick WHAT VAR OPTION...: let the user choose one option, or tell them which variable to set.
pick() {
  local what=$1 var=$2 n i=1 o
  shift 2
  interactive || die "found several ${what}s: $*. Set $var to one of them."
  echo "Found several ${what}s:" >&2
  for o; do echo "  $i) $o" >&2; i=$((i + 1)); done
  while read -r -p "Which one? [1-$#] " n; do
    [[ $n =~ ^[0-9]+$ ]] && ((n >= 1 && n <= $#)) && { echo "${!n}"; return; }
  done
  die "no $what picked"
}

command -v adb >/dev/null || die "adb not found. Install Android platform tools:
  Mac:            brew install android-platform-tools
  Debian/Ubuntu:  sudo apt install adb
  Other:          https://developer.android.com/tools/releases/platform-tools"

if [[ -n "${ANDROID_SERIAL:-}" ]]; then
  SERIAL=$ANDROID_SERIAL
else
  _devices=$(adb devices | awk 'NR>1 && NF>=2 {print $1, $2}')
  _ready=$(awk '$2=="device" {print $1}' <<<"$_devices")
  if [[ -z $_ready ]]; then
    case $_devices in
      *unauthorized*) die "the device hasn't allowed this computer yet. Unlock it, tap Allow on the \"Allow USB debugging?\" prompt, and rerun." ;;
      *offline*)      die "the device is offline. Unplug it, plug it back in, and rerun." ;;
      *)              die "no device found. Turn on USB debugging (Settings > Developer options), plug the device in, and rerun." ;;
    esac
  fi
  if [[ $(grep -c . <<<"$_ready") -eq 1 ]]; then SERIAL=$_ready; else SERIAL=$(pick device ANDROID_SERIAL $_ready) || exit 1; fi
fi

adbsu() { adb -s "$SERIAL" shell "su -c '$*'"; }
# Print a device file as root (empty output if it doesn't exist).
adbcat() { adb -s "$SERIAL" exec-out "su -c 'cat \"$1\" 2>/dev/null; true'"; }

adbsu id 2>/dev/null | grep -q 'uid=0' ||
  die "no root access on $SERIAL. In Magisk, open Superuser and allow Shell (or tap Grant if a prompt showed up on the device), then rerun."

# DroidDeck ships under different package names, so find it by its files rather than its name.
# If several installs are found, only the ones with the required Proton build are offered.
find_droiddeck() {
  local found with_proton
  found=$({ printf 'BASE=%q\nPROTON_SUBDIR=%q\n' "${OW_DATA_ROOT:-/data/user/0}" "$PROTON_SUBDIR"
            cat "$REPO/scripts/find-droiddeck.sh"; } | adb -s "$SERIAL" shell su -c sh | tr -d '\r')
  [[ -n "$found" ]] || die "DroidDeck not found on $SERIAL. Install it and open it once, or set DROIDDECK_PACKAGE."
  with_proton=$(awk '$2==1' <<<"$found")
  [[ -n "$with_proton" ]] && found=$with_proton
  found=$(awk '{print $1}' <<<"$found")
  if [[ $(grep -c . <<<"$found") -eq 1 ]]; then echo "$found"; else pick "DroidDeck install" DROIDDECK_PACKAGE $found; fi
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
# DroidDeck's master copy. It's copied over GAME_ENV at every session start, so both get written.
APP_ENV=$(dirname "$(dirname "$LINUXFS")")/game-environment.json
PROTON_DIR="$LINUXFS/$PROTON_SUBDIR"
