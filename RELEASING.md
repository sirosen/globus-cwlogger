# Releasing Guide

- Create a release branch, `release-X.Y.Z`
- Update the version numbers in `client/setup.py` and `daemon/setup.py`
- Update the changelog, `make prepare-release`
- Add & commit these changes

        git add CHANGELOG.md changelog.d client/setup.py daemon/setup.py
        git commit -m 'Update version and changelog for release'

- Open a release PR, `gh pr create`
- Merge the release PR (after approval)
- Tag the release, `make tag-release`
- Create a GitHub release, `gh release create`

## Versioning

globus-cwlogger uses SemVer.
