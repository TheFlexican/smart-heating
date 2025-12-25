# Smart Heating — Architecture & API Reference

Summary: Smart Heating is a Home Assistant custom integration providing multi-area
heating control. The integration uses Home Assistant areas, climate entities and
sensors to implement schedules, adaptive learning (heating curve), safety checks
and analytics.

Contents
- High-level overview
- Backend components and responsibilities
- Data model and storage
- REST API and WebSocket interfaces (examples)
- Home Assistant service handlers and schemas
- Frontend architecture and important UI flows
- Adaptive learning and control algorithms
- Extensibility, testing and CI, HACS notes

## 1. High-level overview

Actors:
- Home Assistant (core): entity registry, areas, devices, recorder
- Smart Heating backend (this integration): business logic, coordinators, services, API
- Smart Heating frontend: React SPA served from the integration

Runtime flow (simplified):
1. The integration reads configuration and stored data (JSON or DB) on startup.
2. `SmartHeatingCoordinator` subscribes to HA events and polls device states.
3. `AreaManager` holds per-area models (target temperature, schedules, devices).
4. Scheduler & controllers compute effective target temperatures and call device-specific handlers.
5. Frontend communicates with backend via REST + WebSocket for UI updates and controls.

## 2. Backend components (detailed)

- `core.area_manager.AreaManager`
	- Holds the authoritative model for areas: devices, schedules, presets, TRV configs.
	- Persistent storage through a `ConfigManager` / store; exposes `async_save()`.
	- Methods: `get_area()`, `set_area_target_temperature()`, `add_device_to_area()`, `add_schedule_to_area()`.

- `core.coordinator.SmartHeatingCoordinator`
	- Central coordinator for runtime state: polls, debounces changes, exposes `async_request_refresh()`.
	- Responsible for publishing updates over WebSocket and invoking device control handlers.
	- Implements startup grace periods and manual override detection.

- `climate.*` device handlers
	- `climate/devices/*` contains per-device-type handlers (switches, opentherm, TRV handlers).
	- Each handler exposes `async_control_<device_type>()` which applies target temperatures to actual climate entities.

- `services/*` modules
	- Implement Home Assistant service handlers (e.g., `add_schedule`, `set_boost_mode`).
	- Validate payloads using `voluptuous` schemas defined in `services/schemas.py`.

- `storage/config_manager` and `storage/*`
	- Manage persistent storage: JSON file format by default, optional DB backend using HA recorder.
	- Provide import/export, validation and migration logic.

## 3. Data model and storage

Key entities:
- Area: id, name, enabled, devices[], schedules[], presets, safety config, hysteresis, trv config
- Device: id, entity_id, type (climate, valve, switch), capabilities
- Schedule: id, days, start_time, end_time, preset_mode or temperature
- HistoryEntry: timestamped temperature, device state, TRV runtime data

Storage options:
- JSON (default): simple file-based store managed by the integration.
- Database (optional): integration will use Home Assistant recorder DB (MariaDB/Postgres/MySQL) for history retention and analytics.

Migration:
- Bidirectional migration routines validate the incoming format, preserve IDs and timestamps, and create a backup prior to applying.

## 4. REST API (selected endpoints & examples)

Notes: The frontend and external automation can use the REST API. Endpoints require HA auth.

Example: List areas
Request:
```
GET /api/smart_heating/areas
```
Response (200):
```json
{ "areas": [ {"id":"area_1","name":"Living Room","enabled":true,"target_temperature":21.0} ] }
```

Example: Set area temperature
Request:
```
POST /api/smart_heating/areas/{area_id}/temperature
Body: {"temperature": 21.5}
```
Behavior:
- Validates input, updates `AreaManager`, calls `AreaManager.async_save()` and triggers `coordinator.async_request_refresh()`.

Other endpoints (selected):
- `/api/smart_heating/areas/{id}/devices` — add/remove devices
- `/api/smart_heating/areas/{id}/schedules` — CRUD schedules
- `/api/smart_heating/areas/{id}/boost` — enable/disable boost
- `/api/smart_heating/analytics` — efficiency, history, recommendations
- `/api/smart_heating/backup` — export/import config JSON

(See `smart_heating/api/` and `smart_heating/api_handlers/` for full implementation.)

## 5. WebSocket API

Purpose: low-latency updates for the frontend (area status, device states, history streams).

Common commands:
- `smart_heating/subscribe_updates` — server pushes updates when areas change
- `smart_heating/get_areas` — returns the latest snapshot

Data format: JSON objects matching the REST API responses with additional metadata for deltas.

## 6. Home Assistant service handlers

Services are registered under the `smart_heating` domain and use `services/schemas.py` for validation.

Examples (YAML automation snippets):

Set boost from an automation:
```yaml
service: smart_heating.set_boost_mode
data:
	area_id: living_room
	duration_minutes: 60
	temperature: 24
```

Add schedule via service:
```yaml
service: smart_heating.add_schedule
data:
	area_id: bedroom
	start_time: '22:00'
	end_time: '07:00'
	days: [0,1,2,3,4,5,6]
	preset_mode: sleep
```

See `smart_heating/services/*.py` and `smart_heating/services/schemas.py` for the full list and validation.

## 7. Frontend architecture & important UI flows

- SPA served from `frontend/dist` via the integration static file handler.
- Main pages: overview (Zone cards), area detail (Overview, Devices, Schedule, History, Settings), Devices view, Global Settings, Analytics.
- Key UI flows implemented in `frontend/src/pages/*` and components in `frontend/src/components/*`:
	- Device discovery & assignment uses REST endpoints + area snapshots; front-end filters out already-assigned devices.
	- Schedule editor supports cross-day and date-specific rules.
	- Backup/restore triggers validation on the backend and shows a preview before applying.

## 8. Adaptive learning & control algorithms

Heating curve (high-level):
- `heating_curve.HeatingCurve` computes a base flow temperature from outside temperature and area target.
- `heating_curve_manager` accumulates observations (target, outside temp, indoor response) and can autotune a coefficient used in flow calculation.

Autotune & PID adjustments:
- Autotune adapts a coefficient and derivative term over time; PID controller is used optionally per-area to smooth control and prevent oscillation.
- Protection and safety layers (frost protection, open windows) modify final targets before device control.

Effective target computation: the system computes an `effective_target` per area by combining schedule, preset, boost, vacation, learning offset, hysteresis and safety limits.

## 9. Extensibility & adding features

- Add a device handler: create `climate/devices/<handler>.py`, implement capability detection and control methods, and ensure discovery logic in `device_handlers.py` can find it.
- Add a service: define validation schema in `services/schemas.py`, implement handler in `services/`, and register it in `services/__init__.py`.
- Add REST API: add handler in `api_handlers/`, wire in `api/server.py`, and add a frontend client call in `frontend/src/api/`.

## 10. Testing, CI and quality gates

- Backend tests: `pytest` under `tests/unit/`.
- Frontend tests: Vitest/Jest under `smart_heating/frontend/tests/`.
- `tests/run_tests.sh` runs unit tests and coverage; CI enforces minimum coverage for new code.
- Use `tests/conftest.py` fixtures for HA test harness.

## 11. HACS packaging & reviewer notes

For HACS reviewers:
- The integration uses a config flow (`config_flow.py`) with options flow to configure the integration.
- Platforms: climate, switch, sensor. Entities are named using area-aware conventions.
- All services use validated schemas; critical flows have unit tests.
- The frontend is included as static assets and communicates over the documented REST/WebSocket API.

Reviewer checklist:
- Confirm `manifest.json` metadata and HA version compatibility.
- Validate options flow does not expose secrets and validates inputs (e.g., OpenTherm gateway selection).
- Verify no hard-coded credentials.

## 12. Security & performance considerations

- Use HA async best practices; do not block the event loop.
- Offload heavy analytics/autotune tasks or schedule them to run in small batches.
- Validate all REST and import inputs and sanitize stored data.

---
This document summarizes the implementation and extension points. For step-by-step developer guidance see `DEVELOPER.md` and for user-facing quickstarts see `README.md` and `QUICKSTART.md`.
