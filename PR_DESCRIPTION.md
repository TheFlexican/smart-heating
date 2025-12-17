# Fix: disable manual override when area is disabled

This pull request addresses issue #13: Disabled area incorrectly shows as active when preset mode is not used.

What I changed
- **ZoneCard.tsx**: disable the manual-override switch when the area is disabled and skip the API call when toggled while disabled
- **AreaDetail.tsx**: normalize `area.enabled` checks via helper `isEnabledVal`
- **ZoneCard.test.tsx**: added tests for string-enabled handling and to ensure manual-override toggle is disabled and does not call API for disabled areas

Why
- Prevents unexpected transitions to manual mode when a preset is turned off on a disabled area
- Adds unit tests to avoid future regressions

Tests
- All frontend tests pass locally (94 tests)

Fixes: #13