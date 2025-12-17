PR: fix(frontend): disable manual-override when area is disabled (#13)

Summary:
This PR prevents toggling manual override while an area is disabled, avoiding unintended transitions to manual mode when disabling presets on disabled areas.

Changes:
- ZoneCard.tsx: disable the manual override switch when the area is disabled and guard handler.
- ZoneCard.test.tsx: added test asserting the switch is disabled and API not invoked.

All frontend unit tests pass locally.
