# Shared settings. Overrides: ANDROID_SERIAL (pick a device), DROIDDECK_PACKAGE, OW_LINUXFS (testing).
APP="${DROIDDECK_PACKAGE:-com.antutu.benchmark.full}"
LINUXFS="${OW_LINUXFS:-/data/user/0/$APP/files/linuxfs/root}"
COMPONENTS=$LINUXFS/.local/share/droiddeck-components
GAME_ENV=$LINUXFS/.config/droiddeck/game-environment.json
APPID=2357570  # Overwatch 2

PROTON_NAME="Proton Experimental (ARM64)"
PROTON_VERSION=experimental-11.0-20261008-arm64
PROTON_DIR="$LINUXFS/.local/share/Steam/steamapps/common/$PROTON_NAME"
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
