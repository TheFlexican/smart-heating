### Fixed
- Preserve zones overview viewport when updating an area's temperature; avoid large list loader during small updates to prevent scrolling/jumps. (frontend)
- Area cards are no longer clickable; area configuration is now accessible from the area card's three-dots menu (ensures a consistent way to reach settings).

- Safety sensors: preserve multiple configured safety sensors when adding a new sensor via the API (backend). Previously adding a sensor replaced the entire list; now the API adds or updates a single sensor without clearing others. (fix)

### Chore
- Fix WebSocket client/server integration for device logs: register `smart_heating/subscribe_device_logs` on the backend, ensure frontend WebSocket commands include an `id` automatically, and remove a temporary `console.debug` used during debugging. This enables the Global Settings → Device Logs panel to subscribe and receive live device events. (frontend + backend) — See PR #87

Note: PR #87 was merged into `main` on 2025-12-20; these entries ensure the changelog reflects the merge.
