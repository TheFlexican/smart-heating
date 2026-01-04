# Developer Guide: Smart Heating for Home Assistant

This guide is aimed at contributors implementing fixes or features and at reviewers.

## Project structure (quick map)

- `smart_heating/` — Backend Python integration
  - `core/` — area manager, coordinator, controllers
  - `climate/` — device handlers and control logic
  - `services/` — service handlers and schemas
  - `storage/` — config manager and persistence
  - `api/` — REST and WebSocket handlers
- `smart_heating/frontend/` — React + TypeScript SPA
- `tests/` — pytest unit tests for backend; frontend tests under `frontend/tests`
- `scripts/` — useful scripts: `deploy_test.sh`, `setup_test.sh`, `create_backup.sh`

## Developer environment — reproducible steps

1. Create and activate Python virtualenv:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Frontend dependencies:
```bash
cd smart_heating/frontend
npm ci
```

3. (Optional) Start frontend dev server for UI work:
```bash
cd smart_heating/frontend
npm run dev
```

4. Run backend unit tests:
```bash
bash tests/run_tests.sh
```

5. Deploy to a local test HA instance (see `scripts/deploy_test.sh`):
```bash
bash scripts/deploy_test.sh
# then open Home Assistant and install the integration from HACS/local
```

## Debugging tips & common workflows

- Inspect logs:
  - Home Assistant logs (Supervisor → System → Logs) for runtime errors.
  - Per-area logs available in UI (useful for diagnosing control logic).
- Quickly reproduce service calls via `Developer Tools → Services` in HA or `hass-cli`.
- Use `tests/conftest.py` fixtures to create realistic HA entity states in unit tests.
- If a change affects device control, add unit tests that assert `async_control_*` handlers are called with expected values.

## How to add a feature (example: new device handler)

1. Implement handler under `smart_heating/climate/devices/` (use `BaseDeviceHandler` as reference).
2. Add capability discovery logic (see `services/device_handlers.py`).
3. Add unit tests in `tests/unit/` to cover discovery and control behavior.
4. If UI changes are required, modify `frontend/src/components` and add tests under `frontend/tests`.
5. Update documentation (`DEVELOPER.md`, `ARCHITECTURE.md`, and `README.md`) and translations.

## REST & Service integration guidelines

- Use `services/schemas.py` for new service validation.
- REST handlers should remain thin: validate -> call `AreaManager` -> save -> request refresh.
- Always call `coordinator.async_request_refresh()` after state changes to ensure UI and entities update.

## Running and writing tests

- Backend: write pytest unit tests in `tests/unit/`. Use mocks for `hass` and `area_manager` where appropriate.
- Frontend: add tests with Vitest/React Testing Library in `smart_heating/frontend/tests/`.
- Run coverage with `bash tests/run_tests.sh` and examine `coverage_html/index.html`.

## Linters, formatting and pre-commit

- Backend uses `ruff` as the single linter/formatter (pre-commit hooks may run automatically on commit).
- Frontend uses `eslint` and `prettier` - run `npm run lint` under `smart_heating/frontend`.

## CI, quality gating and release notes

- CI expects unit tests to pass and optionally checks coverage thresholds for changed code.
- When preparing a release, update `CHANGELOG.md`, `manifest.json` version and frontend `package.json` version.

## Useful code locations (quick references)

- `smart_heating/core/area_manager.py` — area model and persistence
- `smart_heating/core/coordinator.py` — central coordinator and refresh logic
- `smart_heating/heating_curve.py` & `climate/controllers/heating_curve_manager.py` — learning code
- `smart_heating/services/*.py` — service entrypoints
- `smart_heating/api/*` — REST handlers (match frontend `api/` client)
- `smart_heating/frontend/src/pages` and `.../components` — UI pages and components

## Troubleshooting development issues

- If unit tests fail after refactor, run a targeted test with `pytest tests/unit/test_foo.py -q`.
- For frontend build issues, try `cd smart_heating/frontend && npm ci && npm run build` and examine `vite` output.
- For integration not appearing in HA after deploy: check `custom_components/smart_heating` path, restart HA, and check `config_entries` logs.

## Resources

- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [Testing Home Assistant custom components](https://github.com/home-assistant/core/tree/dev/tests)
- [Material-UI Documentation](https://mui.com/)

---
This file focuses on practical developer workflows; see `ARCHITECTURE.md` for deeper technical design and `README.md`/`QUICKSTART.md` for user-focused guidance.
