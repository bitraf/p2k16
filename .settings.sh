#!/bin/sh

if [ "$0" = "$BASH_SOURCE" ]
then
  echo "This script should be sourced (. $0)"
  exit 1
fi

enable_nvm=1

basedir="$(dirname "${BASH_SOURCE[0]}")"
basedir="$(cd "$basedir" && pwd)"

if [ "$enable_nvm" = 1 ]
then
  if [ ! -r "$HOME"/.nvm/nvm.sh ]
  then
    echo "NVM is not installed ($HOME/.nvm/nvm.sh missing)" > /dev/stderr
  else
    echo Loading NVM
    . "$HOME"/.nvm/nvm.sh
    nvm use
  fi
fi

echo "Adding bin/ to path"
PATH="$basedir/bin:$PATH"

echo "Setting PGPORT and PGHOST."
export PGHOST="${PGHOST-127.0.0.1}"
export PGPORT="${PGPORT-2016}"
export PGPASSFILE="${PGPASSFILE-$(pwd)/.pgpass}"
[ -f "$PGPASSFILE" ] && chmod 0600 "$PGPASSFILE"

echo "Setting FLYWAY_*"
export FLYWAY_URL=jdbc:postgresql://$PGHOST:$PGPORT/p2k16
export FLYWAY_USER=p2k16-flyway
export FLYWAY_PASSWORD=p2k16-flyway
export FLYWAY_SCHEMAS=public
export FLYWAY_VALIDATE_ON_MIGRATE=false
export FLYWAY_LOCATIONS=filesystem:$basedir/migrations
export FLYWAY_TABLE=schema_version
