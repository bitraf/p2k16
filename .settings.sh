#!/bin/sh

enable_nvm=1

basedir=$(dirname "$_")
basedir=$(cd "$basedir" && pwd)

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

echo "Adding tools/ to path"
PATH="$basedir/tools:$PATH"

echo "Setting PGPORT and PGHOST."
export PGPORT=2016
export PGHOST=localhost
