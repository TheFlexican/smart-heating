Fix: disable manual-override when area is disabled

This PR prevents toggling manual override while an area is disabled, which could otherwise cause the zone to switch to manual mode unexpectedly when disabling presets. The change disables the `Switch` control when the area is disabled and guards the handler to avoid server calls. Added a unit test verifying the control is disabled and the API is not called.

Files changed:
- src/components/ZoneCard.tsx
- src/components/ZoneCard.test.tsx

All frontend tests pass locally.
