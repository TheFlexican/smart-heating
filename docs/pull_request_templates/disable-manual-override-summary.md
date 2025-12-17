## Fix: Disable manual-override toggle when area is disabled

### Summary
This PR prevents a user from toggling Manual Override when the area is disabled. If an area is disabled but a preset is active, disabling the preset previously could cause the zone to unexpectedly enter manual mode (or schedule) because the manual-override toggle could still be interacted with. To avoid this, the manual override switch is now disabled when an area is disabled and the onChange handler short-circuits if the area is not enabled.

### Changes
- **Frontend:** `ZoneCard.tsx`
  - Added `disabled={!enabled}` to the manual override `Switch` and a guard in the onChange handler to prevent API calls when area is disabled.
  - Introduced `isEnabledVal` helper where appropriate to normalize `enabled` values (accepts boolean true or string 'true').
- **Tests:** `ZoneCard.test.tsx`
  - Added a test asserting that the manual override switch is disabled for disabled areas and that the `setManualOverride` API is not called.

### Why
This avoids the previously observed state transition where the UI could change to manual mode when disabling a preset for an already-disabled area.

### Notes
- All frontend unit tests pass locally.
- No backend changes required.

Fixes: #13
