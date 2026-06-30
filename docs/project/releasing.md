# Releasing

## Release process

You release tmuxp by tagging a version: pushing a `v<version>` tag triggers a CI
workflow that builds the package and publishes it to PyPI via OIDC trusted
publishing.

1. Update `CHANGES` with the release notes.
2. Bump the version in `src/tmuxp/__about__.py`.
3. Commit the bump:

   ```console
   $ git commit -m "Tag v<version>"
   ```

4. Tag it:

   ```console
   $ git tag v<version>
   ```

5. Push the commit and the tag:

   ```console
   $ git push && git push --tags
   ```

6. CI builds and publishes to PyPI automatically.

## Changelog format

`CHANGES` is rendered as the changelog page. Each release is a Markdown section
headed by its version and date:

```text
## tmuxp <version> (<date>)

### Breaking changes

- Description of the break, with a migration path (#issue)

### What's new

- Description of the feature (#issue)

### Fixes

- Description of the fix (#issue)
```

Subheadings appear in a fixed order when present: `### Breaking changes`,
`### Dependencies`, `### What's new`, `### Fixes`, `### Documentation`,
`### Development`.
