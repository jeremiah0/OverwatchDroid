# Runs on the device as root (piped in by env.sh). Expects BASE and PROTON_SUBDIR to be set.
# Prints one line per app data dir that looks like DroidDeck: "<package> <0|1>",
# where 1 means the required Proton build's folder is installed in it.
for files in "$BASE"/*/files; do
  root="$files/linuxfs/root"
  [ -d "$root" ] || continue
  [ -e "$files/droiddeck-esync" ] || [ -d "$root/.config/droiddeck" ] ||
    [ -d "$root/.local/share/droiddeck-components" ] || continue
  pkg=${files%/files}; pkg=${pkg##*/}
  if [ -f "$root/$PROTON_SUBDIR/version" ]; then echo "$pkg 1"; else echo "$pkg 0"; fi
done
