#!/bin/bash

set -euo pipefail
cd "$(dirname "$0")"

if [ $# -ne 1 ]; then
  echo "USAGE: ./publish-github-assets.sh RELEASE_TAG" >&2
  exit 2
fi
RELEASE_TAG="$1"

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
  gh release upload "$RELEASE_TAG" "$name.tar.gz"
  popd
done
