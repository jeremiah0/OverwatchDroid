#!/usr/bin/env bash
# The normal setup runs inside DroidDeck's Linux desktop. Legacy ADB remains opt-in.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
if [[ ${1:-} == --legacy ]]; then
  shift
  exec bash "$here/legacy-install.sh" "$@"
fi
# Preserve the old uninstall command; it restores only the October ntdll.
if [[ ${1:-} == --uninstall ]]; then
  exec bash "$here/legacy-install.sh" "$@"
fi
command -v python3 >/dev/null || {
  echo "Python 3 is needed. Open Konsole in DroidDeck's Linux desktop and install python3 with its package manager." >&2
  exit 1
}
case ${1:-} in
  --legacy-runtime)
    shift
    exec python3 -I "$here/runtime_patch.py" --proton "$@"
    ;;
  --restore-runtime)
    shift
    exec python3 -I "$here/runtime_patch.py" --restore "$@"
    ;;
esac
exec python3 -I "$here/setup.py" "$@"
