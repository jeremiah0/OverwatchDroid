# Shared paths for the Thor. Override the device with ANDROID_SERIAL=...
SERIAL="${ANDROID_SERIAL:-65636070}"
APP=com.antutu.benchmark.full
LINUXFS=/data/user/0/$APP/files/linuxfs/root
COMPONENTS=$LINUXFS/.local/share/droiddeck-components
GAME_ENV=$LINUXFS/.config/droiddeck/game-environment.json
APPID=2357570  # Overwatch 2

STORE_DIRS=(
  ntdll-pr47-experimental-11.0-20261008
  original-Proton_Experimental_ARM64-experimental-11.0-20261008-arm64-ntdll
  FEXCore-2610-d2rfix28-linux
)

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
adbsu() { adb -s "$SERIAL" shell "su -c '$*'"; }
