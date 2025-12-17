## ✅ Fix disabled area preset/manual behavior

This PR ensures that the manual override control can't be toggled when an area is disabled. Previously, turning off a preset via the area card while the area was disabled could unexpectedly switch the area into manual mode. This change:

- Disables the **manual override** switch when an area is disabled
- Prevents the `setManualOverride` API call from being executed in that case
- Adds unit tests to cover the behavior (ZoneCard tests)
- Normalizes `area.enabled` checks to accept both boolean and string representations (e.g., `'true'`/`'false'`)

Tests: all frontend tests pass locally (94 tests)

Fixes: #13