#!/bin/bash

set -euo pipefail
cd "$(dirname "$0")"

GHAPI="https://api.github.com"
GHUPLOADS="https://uploads.github.com"
REPO_PATH="repos/globus/globus-cwlogger"

echo "= Startup & Self-Check"

command -v jq > /dev/null 2>&1 || { echo "requires jq"; exit 2; }

RELEASE_PATH="latest"
[ $# -gt 0 ] && RELEASE_PATH="tags/$1"
[ -f "$HOME/.github-token" ] || { echo "Must have a token in ~/.github-token"; exit 2; }

AUTH_H="Authorization: token $(cat "$HOME"/.github-token)"
RELEASE_ID="$(curl -s -H "$AUTH_H" "${GHAPI}/$REPO_PATH/releases/$RELEASE_PATH" | jq '.id' -r)"
echo "RELEASE_ID=$RELEASE_ID"

ASSET_URL="$GHUPLOADS/$REPO_PATH/releases/$RELEASE_ID/assets"
echo "ASSET_URL=$ASSET_URL"

# build and upload client and daemon packages
for name in client daemon; do
  pushd "$name"
  echo "= $name = Clean any past run"
  rm -rf ./dist/
  rm -f ./$name.tar.gz

  echo "= $name = Build"
  python setup.py sdist
  glob=(dist/*.tar.gz)
  TARBALL="${glob[0]}"
  echo "TARBALL=$TARBALL"

  echo "= $name = Rename"
  mv "$TARBALL" "$name.tar.gz"

  echo "= $name = Upload"
  curl -Ssf -XPOST \
      -H "Authorization: token $(cat "$HOME"/.github-token)" \
      -H "Content-Type: application/gzip" \
      "${ASSET_URL}?name=$name.tar.gz" --data-binary @"$name.tar.gz"
  popd
done
