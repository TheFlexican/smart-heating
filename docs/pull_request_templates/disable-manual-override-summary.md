Title: fix(frontend): disable manual-override when area is disabled (#13)

This PR prevents toggling manual override while the area is disabled, avoiding unintended transitions to manual mode when disabling presets on disabled areas.

Changes:
- ZoneCard.tsx: disable the manual override switch when the area is disabled and guard the onChange handler.
- ZoneCard.test.tsx: added a test to assert the switch is disabled and the API is not invoked.

All frontend unit tests pass locally. No backend changes required.
