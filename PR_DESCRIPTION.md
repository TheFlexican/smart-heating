Fixes #13 - Disabled area incorrectly shows as active when preset mode is not used.

### Summary
This PR ensures manual override cannot be toggled when an area is disabled. It also normalizes enabled checks and adds tests to prevent regressions.

Changes:
- `ZoneCard.tsx`: disable manual override switch for disabled areas and guard onChange
- `AreaDetail.tsx`: normalized enabled checks via helper
- `ZoneCard.test.tsx`: added tests to cover string-enabled and disabled-manual behavior

All tests pass locally.

Fixes: #13