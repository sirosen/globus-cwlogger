# Releasing Guide

- Create a release branch, `release-YY.N` (see the [versioning section](#versioning))
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

As of 2024-08-28, globus-cwlogger uses a simple CalVer variant.
Version numbers are a two-digit year and a release number.

The first release of 2025 is `25.1`, the second one is `25.2`, and so forth.
