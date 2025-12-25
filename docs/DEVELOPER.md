... (no functional change, re-iterate new-code coverage rule in docs)

- New requirement: New or changed lines added to the codebase must have at least 80% coverage on the diff. This is enforced by `.github/workflows/enforce-new-code-coverage.yml` using diff-cover.
