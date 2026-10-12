#!/usr/bin/env bash
# Install the repo's store components onto the Thor.
#   push.sh            store dirs only (ntdll pr47, original ntdll, d2rfix FEX)
#   push.sh --config   also overwrite desired.tsv and game-environment.json
# Device copies of anything overwritten are saved to /data/local/tmp/ow-push-<timestamp>/.
set -euo pipefail
source "$(dirname "$0")/env.sh"
cd "$REPO"

stamp=$(date +%Y%m%d-%H%M%S)
bak=/data/local/tmp/ow-push-$stamp
stage=/data/local/tmp/ow-stage-$stamp

# Ownership and SELinux label come from desired.tsv, which DroidDeck itself wrote.
owner=$(adbsu "stat -c %u:%g $COMPONENTS/desired.tsv" | tr -d '\r')
label=$(adbsu "ls -Z $COMPONENTS/desired.tsv" | awk '{print $1}' | tr -d '\r')
echo "owner $owner, label $label"

adb -s "$SERIAL" shell "mkdir -p $stage"
tar -C store -cf - "${STORE_DIRS[@]}" | adb -s "$SERIAL" shell "tar -C $stage -xf -"
if [[ "${1:-}" == "--config" ]]; then
  adb -s "$SERIAL" push config/desired.tsv config/game-environment.json "$stage/" >/dev/null
fi

adbsu "
  set -e
  mkdir -p $bak
  for d in ${STORE_DIRS[*]}; do
    [ -d $COMPONENTS/store/\$d ] && cp -a $COMPONENTS/store/\$d $bak/
    rm -rf $COMPONENTS/store/\$d
    cp -r $stage/\$d $COMPONENTS/store/
    chown -R $owner $COMPONENTS/store/\$d
    chmod -R go-rwx $COMPONENTS/store/\$d
    chcon -R $label $COMPONENTS/store/\$d
  done
  if [ -f $stage/desired.tsv ]; then
    cp -a $COMPONENTS/desired.tsv $GAME_ENV $bak/
    cat $stage/desired.tsv > $COMPONENTS/desired.tsv
    cat $stage/game-environment.json > $GAME_ENV
  fi
  rm -rf $stage
"
echo "previous device copies saved to $bak"
"$REPO/scripts/verify.sh"
