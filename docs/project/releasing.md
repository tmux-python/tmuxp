# Releasing

## Release Process

Releases are triggered by git tags and published to PyPI via OIDC trusted publishing.

1. Update `CHANGES` with the release notes

2. Bump version in `src/tmuxp/__about__.py`

3. Commit:

   ```console
   $ git commit -m "tmuxp <version>"
   ```

4. Tag:

   ```console
   $ git tag v<version>
   ```

5. Push:

   ```console
   $ git push && git push --tags
   ```

6. CI builds and publishes to PyPI automatically via trusted publishing

## Changelog Format

The `CHANGES` file uses this format:

```text
tmuxp <version> (<date>)
------------------------

### What's new

- Description of feature (#issue)

### Bug fixes

- Description of fix (#issue)

### Breaking changes

- Description of break, migration path (#issue)
```
