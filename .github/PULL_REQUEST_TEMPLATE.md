### PR: Disable manual override when area is disabled

**Summary**
- Disables `manual override` toggle when an area is disabled so toggling presets while disabled does not unexpectedly switch the area to manual mode.
- Normalizes `area.enabled` checks to accept both boolean and string forms.
- Adds unit tests to cover disabled behavior and string-enabled cases.

**Testing**
- All frontend tests pass locally (94 tests)

**Closes**
- Fixes #13
