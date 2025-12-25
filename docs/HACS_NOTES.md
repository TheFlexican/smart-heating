# HACS & Packaging Notes — Smart Heating

This file is a concise checklist and guidance for HACS reviewers and packagers.

## Purpose
Provide a quick checklist to verify the integration is safe, follows HA patterns, and is HACS-ready.

## Manifest & Metadata
- `manifest.json` must include correct `name`, `domain`, `version`, `requirements` and `homeassistant` version compatibility.
- No hard-coded credentials or tokens in the repo.

## Config Flow
- `config_flow.py` implements the integration setup and offers optional OpenTherm gateway selection when present.
- Options flow exists and validates inputs (e.g., history retention, frost protection defaults).

## Platforms & Entities
- Platforms provided: `climate`, `sensor`, `switch`.
- Entities follow area-aware naming and unique ids.

## Services
- Services are registered under the `smart_heating` domain and validated using `voluptuous` schemas in `services/schemas.py`.
- Service examples are present in `README.md` and documented in `ARCHITECTURE.md`.

## Frontend
- React SPA built into `frontend/dist` and served via static file handler.
- UI communicates using REST endpoints under `/api/smart_heating` and a WebSocket subscription for real-time updates.

## Data & Storage
- Default storage: JSON file managed by the integration.
- Optional storage backend: Home Assistant recorder DB (MariaDB/Postgres/MySQL).
- Migration scripts provide backups and validation steps.

## Security
- Validate and sanitize all external inputs (REST payloads, import JSON).
- Do not expose long-lived tokens or API keys in logs or UI.

## Tests
- Unit tests exist under `tests/unit/` for backend service handlers and core logic.
- Frontend tests under `smart_heating/frontend/tests/`.
- CI enforces tests and coverage for changes.

## Reviewer checklist
- [ ] `manifest.json` metadata looks correct
- [ ] Integration installs via HACS/manual copy and shows UI in HA
- [ ] `config_flow.py` options are safe and validated
- [ ] No secrets or credentials in repo
- [ ] Services have schemas and tests
- [ ] Frontend static files are present and API endpoints documented

---
Add this file to the repository for HACS reviewers and to guide packaging and release.
