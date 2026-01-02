
# Changelog

## [Unreleased]
- refactor: Decompose `GlobalSettings.tsx` into smaller components per tab and helpers to improve maintainability and testability (Presets, Sensors, Safety, Advanced, OpenTherm, Debug, Header, TabPanel).
- tests: Add unit tests for each new component and ensure lint/format passes.

### Bug Fixes & Improvements
- fix(websocket): Prevent false positive ping/pong timeout disconnections (#issue)
  - Fixed issue where WebSocket connections disconnected every 30 seconds
  - Root cause: Timeout check was triggered before first ping was sent
  - Solution: Track when pings are sent and only check for missing pongs after at least one ping has been sent
  - Added test coverage for ping/pong keepalive mechanism

## [v1.0.0] - 2025-12-25
- Initial release
